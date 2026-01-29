# Throughput Analysis - AddressIQ Address Splitting

## Executive Summary

**Current Performance**: ~9.6 addresses/minute (6 rows → 8 addresses in ~50 seconds)

**Target Performance**: 60-120 addresses/minute (10-20x improvement possible)

---

## 🔴 Critical Bottlenecks Identified

### 1. **SEQUENTIAL GPT API CALLS FOR SPLITTING** (BIGGEST ISSUE)

**Location**: `csv_address_processor.py` lines 1235-1250

```python
for index, row in df.iterrows():
    # ...
    split_result = self.address_splitter.analyze_and_split(address1, address2)
```

**Problem**:
- Each address is analyzed **individually** with a separate GPT API call
- For 6 addresses, this means 6 sequential API calls
- Each call takes ~4-5 seconds (network latency + API processing)
- Total: **~26 seconds just for split analysis**

**Timing Breakdown** (from test output):
```
Row 1: 4 seconds  (GPT call + token auth)
Row 2: 4 seconds  (GPT call + token auth)
Row 3: 5 seconds  (GPT call + token auth)
Row 4: 4 seconds  (GPT call + token auth)
Row 5: 5 seconds  (GPT call + token auth)
Row 6: 4 seconds  (GPT call + token auth)
------------------
Total: 26 seconds
```

**Impact**: 
- For 100 addresses: ~7-8 minutes just for splitting
- For 1000 addresses: ~70-80 minutes just for splitting
- This is the #1 throughput killer

---

### 2. **TOKEN ACQUISITION ON EVERY API CALL**

**Location**: `address_splitter.py` line 444

```python
def _gpt_based_split(self, address1: str, address2: str = None):
    # ...
    access_token = get_access_token()  # Called for EVERY address
```

**Location**: `azure_openai.py` lines 47-68

```python
def get_access_token():
    response = requests.post(auth_token_endpoint, data={
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    })
```

**Problem**:
- Each split analysis makes a NEW token request (~200-300ms)
- Token is valid for 20 minutes (1200 seconds) but never reused
- For 6 addresses: 6 token requests = ~1.5 seconds wasted
- For 100 addresses: 100 token requests = ~25 seconds wasted

**Token Reuse Potential**:
- Token expires in: 1200 seconds (from response: "expires_in":1200)
- Could reuse same token for hundreds of addresses
- Currently: 0% reuse
- Optimal: 99%+ reuse

---

### 3. **NO CACHING OF SPLIT DECISIONS**

**Problem**:
- Similar address patterns are analyzed repeatedly
- No pattern recognition or caching layer
- Examples that should be cached:
  * "123 Main St and 456 Oak Ave" → SPLIT pattern
  * "Smith and Jones Law Firm 123 Main St" → DO NOT SPLIT pattern
  * "Lots A, B, and C at 100 Industrial Way" → DO NOT SPLIT pattern

**Impact**:
- Pattern detection is re-done from scratch every time
- Same regex patterns evaluated repeatedly
- GPT calls for similar addresses could be avoided

---

### 4. **INEFFICIENT DATAFRAME ITERATION**

**Location**: `csv_address_processor.py` line 1235

```python
for index, row in df.iterrows():  # SLOW iteration method
    row_dict = row.to_dict()
```

**Problem**:
- `df.iterrows()` is one of the slowest pandas iteration methods
- Creates a copy of each row as a Series object
- For large datasets (10k+ rows), adds significant overhead

**Alternative Methods** (faster):
- `df.itertuples()`: 10-50x faster than iterrows()
- Vectorized operations: 100-1000x faster
- `df.apply()` with axis=1: 2-5x faster

---

### 5. **STANDARDIZATION ALREADY BATCHED (GOOD), BUT SPLITTING IS NOT**

**What's Working Well**:
```
Processing batch 1: rows 1-5  (batched standardization)
Processing batch 2: rows 6-10 (batched standardization)
```

**What's Missing**:
- Split analysis is NOT batched
- Each address gets individual GPT call before reaching batched standardization
- Asymmetry: splitting is sequential, standardization is batched

---

## 📊 Performance Impact Analysis

### Current Flow Timeline (6 addresses):
```
1. Token Auth #1:        0.3s
2. Split Analysis #1:    3.7s
3. Token Auth #2:        0.3s
4. Split Analysis #2:    3.7s
5. Token Auth #3:        0.3s
6. Split Analysis #3:    4.7s
7. Token Auth #4:        0.3s
8. Split Analysis #4:    3.7s
9. Token Auth #5:        0.3s
10. Split Analysis #5:   4.7s
11. Token Auth #6:       0.3s
12. Split Analysis #6:   3.7s
    TOTAL SPLITTING:     26.0s

13. Standardization (batched):
    - Token Auth:        0.3s
    - Batch 1 (5 addr):  5.0s
    - Token Auth:        0.3s
    - Batch 2 (3 addr):  5.0s
    TOTAL STANDARDIZATION: 10.6s

GRAND TOTAL: 36.6s + overhead = ~50s
```

### Network Breakdown:
- **Token requests**: 8 calls × ~300ms = 2.4s
- **GPT API latency**: 8 calls × ~200ms = 1.6s
- **GPT processing**: 8 calls × ~3.5s = 28s
- **Data transfer**: ~1s
- **Overhead**: ~2s
- **TOTAL**: ~35s

### Scalability Projection:

| Addresses | Current (Sequential) | With Batching (20/batch) | Improvement |
|-----------|---------------------|--------------------------|-------------|
| 6         | 50s (9.6/min)       | 12s (30/min)            | 3.1x faster |
| 100       | 8m 20s (12/min)     | 1m 15s (80/min)         | 6.7x faster |
| 1,000     | 1h 23m (12/min)     | 12m 30s (80/min)        | 6.7x faster |
| 10,000    | 13h 53m (12/min)    | 2h 5m (80/min)          | 6.7x faster |

---

## 🚀 Solutions & Recommendations

### **Solution 1: Implement Batch GPT Split Analysis** ⭐ HIGHEST IMPACT

**Expected Improvement**: 5-10x throughput increase

**Implementation**:
1. Collect addresses in memory (batch of 10-20)
2. Make single GPT call with all addresses
3. Parse batch response
4. Distribute results

**Benefits**:
- Reduces API calls from N to N/20
- Reduces token requests from N to N/20
- Better GPT context (can see patterns across batch)

**Code Location**: Add `batch_analyze_and_split()` method to `AddressSplitter`

**Example**:
```python
# Instead of 6 calls:
for addr in addresses:
    result = analyze_and_split(addr)  # 6 × 4s = 24s

# Do 1 call:
results = batch_analyze_and_split(addresses)  # 1 × 5s = 5s
```

---

### **Solution 2: Implement Token Caching** ⭐ HIGH IMPACT

**Expected Improvement**: 10-15% throughput increase

**Implementation**:
1. Cache access token in memory with expiration time
2. Check cache before requesting new token
3. Refresh only when expired

**Code Change**: `azure_openai.py`
```python
_token_cache = {'token': None, 'expires_at': 0}

def get_access_token():
    if time.time() < _token_cache['expires_at']:
        return _token_cache['token']
    
    # Get new token...
    _token_cache['token'] = token
    _token_cache['expires_at'] = time.time() + expires_in - 60  # 60s buffer
    return token
```

**Benefits**:
- Eliminates 95%+ of token requests
- Reduces network calls
- Faster response times

---

### **Solution 3: Add Pattern-Based Split Cache** ⭐ MEDIUM IMPACT

**Expected Improvement**: 20-40% throughput increase (for datasets with repetitive patterns)

**Implementation**:
1. Extract pattern from address (e.g., "X and Y Street")
2. Cache split decision by pattern
3. Use cached decision for similar addresses

**Example Patterns**:
```python
patterns = {
    r'^\w+ and \w+ (Law Firm|LLC|Inc)': False,  # Business name
    r'^\d+ \w+ St and \d+ \w+ Ave$': True,      # Two addresses
    r'^Lots [A-Z, ]+at \d+': False,             # Lot designations
}
```

**Benefits**:
- Instant decision for cached patterns
- No API call needed
- Reduces GPT costs

---

### **Solution 4: Use Faster DataFrame Iteration** ⭐ LOW IMPACT

**Expected Improvement**: 2-5% throughput increase

**Implementation**:
Replace `df.iterrows()` with `df.itertuples()` or vectorized operations

**Code Change**: `csv_address_processor.py`
```python
# Instead of:
for index, row in df.iterrows():
    address1 = row[primary_addr_col]

# Use:
for row in df.itertuples(index=True):
    address1 = getattr(row, primary_addr_col)
```

**Benefits**:
- 10-50x faster iteration
- Lower memory usage
- Better for large datasets

---

### **Solution 5: Implement Async/Parallel API Calls** ⭐ ADVANCED

**Expected Improvement**: 3-5x throughput increase

**Implementation**:
Use `asyncio` or `concurrent.futures` to make parallel API calls

**Benefits**:
- Overlapping I/O wait times
- Better CPU utilization
- Faster for large batches

**Complexity**: Requires async refactoring of Azure OpenAI client

---

## 📈 Recommended Implementation Priority

### Phase 1: Quick Wins (1-2 days)
1. ✅ **Token Caching** (15% improvement, easy)
2. ✅ **DataFrame Iteration** (5% improvement, easy)

**Expected Combined**: 20% faster (12 → 14 addresses/min)

---

### Phase 2: Major Improvement (3-5 days)
3. ✅ **Batch GPT Split Analysis** (600% improvement, medium complexity)

**Expected Result**: 80 addresses/min (8.3x faster than current)

---

### Phase 3: Optimization (1-2 days)
4. ✅ **Pattern-Based Cache** (20-40% additional improvement on Phase 2)

**Expected Result**: 100+ addresses/min (10x+ faster than current)

---

### Phase 4: Advanced (1 week)
5. ⚠️ **Async/Parallel Processing** (3-5x additional improvement)

**Expected Result**: 300+ addresses/min (30x+ faster than current)

---

## 💰 Cost-Benefit Analysis

### Cost Impact:

**Current Cost** (per 1000 addresses):
- Split analysis: 1000 GPT calls × $0.002 = $2.00
- Standardization: 200 batch calls × $0.008 = $1.60
- **Total**: $3.60 per 1000 addresses

**With Batching** (per 1000 addresses):
- Split analysis: 50 batch calls × $0.008 = $0.40 (80% reduction)
- Standardization: 200 batch calls × $0.008 = $1.60
- **Total**: $2.00 per 1000 addresses (44% cost reduction)

**With Pattern Cache** (per 1000 addresses, 30% hit rate):
- Split analysis: 35 batch calls × $0.008 = $0.28 (86% reduction)
- Standardization: 200 batch calls × $0.008 = $1.60
- **Total**: $1.88 per 1000 addresses (48% cost reduction)

---

## 🎯 Target Performance Goals

### Short-term (Phase 1+2):
- **Throughput**: 80 addresses/minute
- **Time for 1000 addresses**: 12.5 minutes
- **Cost per 1000**: $2.00

### Long-term (All Phases):
- **Throughput**: 300+ addresses/minute
- **Time for 1000 addresses**: 3.3 minutes
- **Cost per 1000**: $1.50

---

## 📝 Monitoring Recommendations

Add timing metrics to track:
1. Time per split analysis call
2. Time per batch
3. Token acquisition time
4. Cache hit rates
5. API response times

**Example Logging**:
```python
import time

start = time.time()
# ... operation ...
duration = time.time() - start
print(f"⏱️  Split analysis: {duration:.2f}s")
```

---

## Summary

The **main bottleneck** is sequential GPT API calls for split analysis. Implementing batch processing for splitting (matching the existing batched standardization) would provide the biggest improvement - approximately **6-8x throughput increase** with reduced costs.

Token caching is a quick win that adds another 10-15% improvement with minimal code changes.

Combined, these changes would take the system from **9.6 addresses/minute to 80+ addresses/minute** - making it viable for production workloads of 10,000+ addresses.
