import React, { useState, useEffect, useRef, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import '../../styles/shared.css';
import './RegionCityMap.css';
import api from '../../services/api';

// Add keyframes for spinner animation
const spinnerStyle = document.createElement('style');
spinnerStyle.innerHTML = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;
if (!document.head.querySelector('style[data-spinner]')) {
  spinnerStyle.setAttribute('data-spinner', 'true');
  document.head.appendChild(spinnerStyle);
}

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface LocationData {
  site_pk: number;
  site_name: string;
  full_address: string;
  latitude: number;
  longitude: number;
}

// Component to handle map updates and prevent black screen issue
const MapUpdater: React.FC<{ center: [number, number]; zoom: number }> = ({ center, zoom }) => {
  const map = useMap();
  
  useEffect(() => {
    // Invalidate size when component mounts or updates
    const invalidateMap = () => {
      // Call invalidateSize multiple times to ensure map renders properly
      map.invalidateSize();
      
      // Additional invalidation after a short delay
      setTimeout(() => {
        map.invalidateSize();
      }, 100);
      
      // Fly to new position smoothly if there are locations
      if (center[0] !== 20 || center[1] !== 0) {
        map.setView(center, zoom, { animate: true, duration: 1 });
      }
    };

    invalidateMap();

    // Handle visibility change to fix black screen on tab switch
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        setTimeout(() => {
          map.invalidateSize();
        }, 100);
      }
    };

    // Listen for visibility changes
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Also listen for window resize
    const handleResize = () => {
      map.invalidateSize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('resize', handleResize);
    };
  }, [map, center, zoom]);

  return null;
};

const RegionCityMap: React.FC = () => {
  const [selectedCountry, setSelectedCountry] = useState('');
  const [availableCountries, setAvailableCountries] = useState<string[]>([]);
  const [locations, setLocations] = useState<LocationData[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingCountries, setLoadingCountries] = useState(true);
  const [error, setError] = useState<string>('');
  const mapContainerRef = useRef<HTMLDivElement>(null);

  // Handle visibility change to fix black screen issue on tab switch
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && mapContainerRef.current) {
        // Force re-render map tiles when tab becomes visible
        setTimeout(() => {
          window.dispatchEvent(new Event('resize'));
        }, 100);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // Fetch available countries on component mount
  useEffect(() => {
    const fetchCountries = async () => {
      setLoadingCountries(true);
      try {
        const response = await api.get('/countries');
        if (response.data && response.data.countries) {
          setAvailableCountries(response.data.countries);
        }
      } catch (err) {
        console.error('Error fetching countries:', err);
        setError('Failed to load countries. Please try again.');
      } finally {
        setLoadingCountries(false);
      }
    };

    fetchCountries();
  }, []);

  const handleCountryChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCountry(event.target.value);
    setLocations([]);
    setError('');
  };

  const fetchLocations = async () => {
    if (!selectedCountry) {
      setError('Please select a country');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.get('/coordinates', {
        params: { country: selectedCountry }
      });
      
      if (response.data && response.data.coordinates) {
        setLocations(response.data.coordinates);
        if (response.data.coordinates.length === 0) {
          setError(`No locations found for ${selectedCountry}`);
        }
      }
    } catch (err: any) {
      console.error('Error fetching locations:', err);
      setError(err.response?.data?.error || 'Failed to fetch locations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = () => {
    fetchLocations();
  };

  // Memoize map center and zoom to prevent unnecessary recalculations
  const mapCenter = useMemo((): [number, number] => {
    if (locations.length === 0) return [20, 0];
    
    const avgLat = locations.reduce((sum, loc) => sum + loc.latitude, 0) / locations.length;
    const avgLng = locations.reduce((sum, loc) => sum + loc.longitude, 0) / locations.length;
    
    return [avgLat, avgLng];
  }, [locations]);

  const mapZoom = useMemo((): number => {
    if (locations.length === 0) return 2;
    if (locations.length === 1) return 10;
    
    const latitudes = locations.map(loc => loc.latitude);
    const longitudes = locations.map(loc => loc.longitude);
    
    const latSpread = Math.max(...latitudes) - Math.min(...latitudes);
    const lngSpread = Math.max(...longitudes) - Math.min(...longitudes);
    const maxSpread = Math.max(latSpread, lngSpread);
    
    if (maxSpread < 0.1) return 12;
    if (maxSpread < 0.5) return 10;
    if (maxSpread < 1) return 9;
    if (maxSpread < 3) return 8;
    if (maxSpread < 5) return 7;
    if (maxSpread < 10) return 6;
    if (maxSpread < 20) return 5;
    if (maxSpread < 40) return 4;
    return 3;
  }, [locations]);

  // Use ref to track if map has been initialized
  const mapInitialized = useRef(false);

  useEffect(() => {
    if (locations.length > 0) {
      mapInitialized.current = true;
    }
  }, [locations]);

  // Fix for initial map render - force invalidate size on mount
  useEffect(() => {
    const timer = setTimeout(() => {
      window.dispatchEvent(new Event('resize'));
    }, 100);
    
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="modern-container">
      {/* Hero Section */}
      <div className="modern-hero">
        <h1 className="modern-hero-title">Map View</h1>
        <p className="modern-hero-subtitle">Visualize site locations with geographical coordinates</p>
      </div>

      {/* Main Card */}
      <div className="modern-card">
        {loadingCountries ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p className="loading-text">Loading countries...</p>
          </div>
        ) : (
          <>
            {/* Info Card */}
            <div className="modern-info-cards">
              <div className="modern-info-card modern-info-card-amber">
                <div className="modern-info-card-content">
                  <div className="modern-info-card-title">Test Data Notice</div>
                  <div className="modern-info-card-text">The locations and coordinates displayed are for testing and illustration purposes only. Verify coordinates independently before production use.</div>
                </div>
              </div>
            </div>

            {/* Country Selection Controls */}
            <div className="map-controls">
              <div className="control-group">
                <label className="modern-label">Select Country</label>
                <select 
                  value={selectedCountry} 
                  onChange={handleCountryChange}
                  disabled={availableCountries.length === 0}
                  className="modern-select"
                >
                  <option value="">
                    {availableCountries.length === 0 ? 'No countries available' : 'Select Country'}
                  </option>
                  {availableCountries.map((country) => (
                    <option key={country} value={country}>
                      {country}
                    </option>
                  ))}
                </select>
              </div>
              
              <button 
                onClick={handleSubmit} 
                disabled={!selectedCountry || loading}
                className="modern-btn modern-btn-primary"
              >
                {loading && <span className="modern-btn-spinner" />}
                <span>{loading ? 'Loading...' : 'Get Locations'}</span>
              </button>
            </div>

            {error && (
              <div className="modern-alert modern-alert-error">
                {error}
              </div>
            )}

            {locations.length > 0 && (
              <div className="location-count">
                <span className="count-text">Found {locations.length} location{locations.length > 1 ? 's' : ''} in {selectedCountry}</span>
              </div>
            )}
            
            {/* Map Container */}
            <div className="map-wrapper" ref={mapContainerRef}>
              <MapContainer 
                center={mapCenter} 
                zoom={mapZoom} 
                style={{ height: '100%', width: '100%' }}
                key={`${selectedCountry}-${locations.length}`}
                scrollWheelZoom={true}
              >
                <MapUpdater center={mapCenter} zoom={mapZoom} />
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  maxZoom={19}
                />
                {locations.map((location, index) => (
                  <Marker 
                    key={`${location.site_pk}-${index}`} 
                    position={[location.latitude, location.longitude]}
                  >
                    <Popup>
                      <div className="popup-content">
                        <strong className="popup-title">
                          {location.site_name}
                        </strong>
                        <div className="popup-address">
                          {location.full_address}
                        </div>
                        <div className="popup-coords">
                          <strong>Coordinates:</strong><br />
                          Lat: {location.latitude.toFixed(6)}<br />
                          Lng: {location.longitude.toFixed(6)}
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default RegionCityMap;
