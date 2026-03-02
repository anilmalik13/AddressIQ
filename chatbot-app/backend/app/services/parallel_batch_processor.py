"""
Parallel Batch Processor for Address Standardization
=====================================================
This module is the sole owner of the parallel-execution strategy.
It is only invoked when ENABLE_PARALLEL_BATCHING=true in .env.
When that flag is false the original sequential implementation inside
azure_openai.py is used, leaving zero changes to that code path.

Design
------
- ParallelBatchProcessor.process() receives a flat address list and
  coordinates N concurrent calls to the shared _process_address_batch()
  helper that already exists in azure_openai.py.
- Each batch gets its own independent token budget (dynamic_max_tokens
  is calculated inside _process_address_batch per batch).
- Results from all threads are collected, re-ordered by input_index, and
  returned in the original caller's expected format.
- A per-batch fallback to individual processing is preserved so a single
  failing batch never blocks the whole job.

To tune behaviour, adjust only the three .env variables:
    ENABLE_PARALLEL_BATCHING   true | false
    PARALLEL_BATCH_WORKERS     integer  (recommended: 3 → 10)
    PARALLEL_BATCH_TIMEOUT_SECONDS  integer  (recommended: 30)
"""

from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _get_config() -> dict:
    """
    Pull parallel-batching settings from PROMPT_CONFIG when available,
    falling back to env-var defaults so this module is self-contained.
    """
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        from app.config.address_config import PROMPT_CONFIG
        return {
            "batch_size": PROMPT_CONFIG.get("batch_size", 10),
            "max_batch_size": PROMPT_CONFIG.get("max_batch_size", 10),
            "enable_batch_processing": PROMPT_CONFIG.get("enable_batch_processing", True),
            "workers": PROMPT_CONFIG.get("parallel_batch_workers", 3),
            "timeout": PROMPT_CONFIG.get("parallel_batch_timeout_seconds", 30),
        }
    except Exception:
        # Absolute fallback — read directly from env
        return {
            "batch_size": int(os.getenv("PARALLEL_BATCH_SIZE", "10")),
            "max_batch_size": int(os.getenv("PARALLEL_BATCH_SIZE", "10")),
            "enable_batch_processing": True,
            "workers": int(os.getenv("PARALLEL_BATCH_WORKERS", "3")),
            "timeout": int(os.getenv("PARALLEL_BATCH_TIMEOUT_SECONDS", "30")),
        }


def _import_azure_helpers():
    """
    Lazily import helpers from azure_openai to avoid circular imports
    at module load time (azure_openai.py lazy-imports this module too).
    """
    from app.services.azure_openai import _process_address_batch, standardize_address
    return _process_address_batch, standardize_address


# ---------------------------------------------------------------------------
# Core parallel processor
# ---------------------------------------------------------------------------

class ParallelBatchProcessor:
    """
    Runs multiple address batches concurrently against the Azure OpenAI API.

    Usage
    -----
    processor = ParallelBatchProcessor()
    results   = processor.process(address_list, target_country="AU")
    """

    def __init__(self):
        cfg = _get_config()
        self.batch_size: int  = min(cfg["batch_size"], cfg["max_batch_size"])
        self.workers: int     = cfg["workers"]
        self.timeout: int     = cfg["timeout"]   # seconds per batch future
        print(
            f"[ParallelBatchProcessor] Initialised — "
            f"batch_size={self.batch_size}, workers={self.workers}, "
            f"timeout={self.timeout}s"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(
        self,
        address_list: list,
        target_country: str | None = None,
    ) -> list:
        """
        Standardize all addresses using parallel batch API calls.

        Parameters
        ----------
        address_list   : flat list of raw address strings
        target_country : optional ISO country hint forwarded to each batch

        Returns
        -------
        list of standardised address dicts, sorted by input_index,
        matching the format returned by the sequential implementation.
        """
        if not address_list:
            return []

        _process_address_batch, standardize_address = _import_azure_helpers()

        # Split the full list into batch-sized chunks
        batches = self._split_into_batches(address_list)
        total_batches = len(batches)

        print(
            f"[ParallelBatchProcessor] Starting {total_batches} batches "
            f"across {self.workers} parallel workers "
            f"({len(address_list)} total addresses)"
        )

        all_results: list = []
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix="addr_batch") as executor:
            # Map future → (batch_index, batch_start_offset, batch_addresses)
            future_map = {
                executor.submit(
                    _process_address_batch,
                    batch_addresses,
                    target_country,
                    batch_start,        # batch_offset for input_index calculation
                ): (batch_idx, batch_start, batch_addresses)
                for batch_idx, (batch_start, batch_addresses) in enumerate(batches)
            }

            for future in as_completed(future_map, timeout=None):
                batch_idx, batch_start, batch_addresses = future_map[future]
                batch_num = batch_idx + 1

                try:
                    # Retrieve result with a per-batch wall-clock timeout
                    batch_results = future.result(timeout=self.timeout)
                    all_results.extend(batch_results)
                    print(
                        f"[ParallelBatchProcessor] Batch {batch_num}/{total_batches} "
                        f"completed ({len(batch_results)} addresses)"
                    )

                except FuturesTimeoutError:
                    print(
                        f"[ParallelBatchProcessor] Batch {batch_num}/{total_batches} "
                        f"TIMED OUT after {self.timeout}s — falling back to individual processing"
                    )
                    fallback = self._individual_fallback(
                        batch_addresses, batch_start, target_country, standardize_address
                    )
                    all_results.extend(fallback)

                except Exception as exc:
                    print(
                        f"[ParallelBatchProcessor] Batch {batch_num}/{total_batches} "
                        f"FAILED ({exc}) — falling back to individual processing"
                    )
                    fallback = self._individual_fallback(
                        batch_addresses, batch_start, target_country, standardize_address
                    )
                    all_results.extend(fallback)

        elapsed = round(time.time() - start_time, 2)
        print(
            f"[ParallelBatchProcessor] All {total_batches} batches done in {elapsed}s "
            f"({len(all_results)} addresses processed)"
        )

        # Restore original order — parallel threads return in arbitrary order
        all_results.sort(key=lambda r: r.get("input_index", 0))
        return all_results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _split_into_batches(self, address_list: list) -> list[tuple[int, list]]:
        """
        Split a flat list into (batch_start_offset, batch_addresses) tuples.
        batch_start_offset is the index of the first address in that batch
        relative to the full list — used for input_index alignment.
        """
        batches = []
        for start in range(0, len(address_list), self.batch_size):
            end = min(start + self.batch_size, len(address_list))
            batches.append((start, address_list[start:end]))
        return batches

    @staticmethod
    def _individual_fallback(
        batch_addresses: list,
        batch_start: int,
        target_country: str | None,
        standardize_address_fn,
    ) -> list:
        """
        Per-address fallback used when an entire batch call fails or times out.
        Mirrors the fallback logic in the original sequential implementation.
        """
        results = []
        for i, address in enumerate(batch_addresses):
            try:
                result = standardize_address_fn(address, target_country)
                result["input_index"] = batch_start + i
                results.append(result)
            except Exception as exc:
                results.append({
                    "input_index": batch_start + i,
                    "error": str(exc),
                    "original_address": address,
                    "formatted_address": "",
                    "confidence": "low",
                    "issues": ["processing_error"],
                })
        return results
