import React, { useState, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './RegionCityMap.css';
import api from '../../services/api';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface RegionCountryData {
  [region: string]: string[];
}

interface Coordinate {
  latitude: number;
  longitude: number;
  address?: string;
}

const RegionCityMap: React.FC = () => {
  const [selectedRegion, setSelectedRegion] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('');
  const [coordinates, setCoordinates] = useState<Coordinate[]>([]);
  const [loading, setLoading] = useState(false);

  // Define the region-country mapping based on your data
  const regionCountryMapping: RegionCountryData = useMemo(() => ({
    'APAC - East Asia': ['China', 'Japan', 'South Korea', 'Taiwan', 'Hong Kong', 'Mongolia'],
    'APAC - Southeast Asia': ['Singapore', 'Malaysia', 'Indonesia', 'Thailand', 'Vietnam', 'Philippines', 'Myanmar', 'Cambodia', 'Laos', 'Brunei', 'Timor-Leste'],
    'APAC - South Asia': ['India', 'Pakistan', 'Bangladesh', 'Sri Lanka', 'Nepal', 'Bhutan', 'Maldives', 'Afghanistan'],
    'APAC - Oceania': ['Australia', 'New Zealand', 'Papua New Guinea', 'Fiji', 'Other Pacific Islands'],
    'APAC - Central Asia': ['Kazakhstan', 'Uzbekistan', 'Turkmenistan', 'Kyrgyzstan', 'Tajikistan'],
    'EMEA - Europe': ['Germany', 'France', 'Italy', 'Spain', 'UK', 'Switzerland', 'Norway', 'Russia', 'Ukraine', 'Turkey'],
    'EMEA - Middle East': ['UAE', 'Saudi Arabia', 'Israel', 'Qatar', 'Kuwait', 'Oman', 'Bahrain', 'Jordan', 'Lebanon', 'Iraq', 'Iran', 'Syria', 'Yemen'],
    'EMEA - Africa': ['South Africa', 'Nigeria', 'Kenya', 'Egypt', 'Morocco', 'Algeria', 'Ghana', 'Ethiopia', 'Tanzania', 'Uganda', 'Tunisia'],
    'AMER - North America': ['United States', 'Canada', 'Mexico'],
    'AMER - Central America': ['Belize', 'Costa Rica', 'El Salvador', 'Guatemala', 'Honduras', 'Nicaragua', 'Panama'],
    'AMER - Caribbean': ['Antigua and Barbuda', 'Bahamas', 'Barbados', 'Cuba', 'Dominica', 'Dominican Republic', 'Grenada', 'Haiti', 'Jamaica', 'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'Trinidad and Tobago'],
    'AMER - Caribbean Territories': ['Puerto Rico', 'Guadeloupe', 'Martinique', 'Aruba', 'Curaçao', 'Sint Maarten', 'British Virgin Islands', 'Cayman Islands', 'Turks and Caicos Islands', 'Montserrat', 'U.S. Virgin Islands'],
    'AMER - South America': ['Brazil', 'Argentina', 'Chile', 'Colombia', 'Peru', 'Venezuela'],
    'LATAM': ['Mexico', 'Central America', 'Caribbean', 'South America'],
    'NA': ['United States', 'Canada', 'Mexico'],
    'CIS': ['Russia', 'Belarus', 'Kazakhstan', 'Uzbekistan', 'Armenia', 'Azerbaijan'],
    'MENA': ['UAE', 'Saudi Arabia', 'Israel', 'Qatar', 'Kuwait', 'Oman', 'Bahrain', 'Jordan', 'Lebanon', 'Iraq', 'Iran', 'Syria', 'Yemen', 'Egypt', 'Morocco']
  }), []);

  const regions = useMemo(() => Object.keys(regionCountryMapping), [regionCountryMapping]);
  const countries = useMemo(() => 
    selectedRegion ? regionCountryMapping[selectedRegion] || [] : [], 
    [selectedRegion, regionCountryMapping]
  );

  const handleRegionChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedRegion(event.target.value);
    setSelectedCountry('');
    setCoordinates([]);
  };

  const handleCountryChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCountry(event.target.value);
    setCoordinates([]);
  };

  const fetchCoordinates = async (region: string, country: string): Promise<Coordinate[]> => {
    try {
      const response = await api.get(`/coordinates`, {
        params: { region, country }
      });
      return response.data.coordinates || [];
    } catch (error) {
      console.error('Error fetching coordinates:', error);
      // Fallback to mock data for demonstration
      return getMockCoordinates(country);
    }
  };

  // Mock coordinates for demonstration (replace with actual API call)
  const getMockCoordinates = (country: string): Coordinate[] => {
    const mockData: { [key: string]: Coordinate[] } = {
      'India': [
        { latitude: 28.6139, longitude: 77.2090, address: 'New Delhi' },
        { latitude: 19.0760, longitude: 72.8777, address: 'Mumbai' },
        { latitude: 13.0827, longitude: 80.2707, address: 'Chennai' },
        { latitude: 12.9716, longitude: 77.5946, address: 'Bangalore' },
        { latitude: 22.5726, longitude: 88.3639, address: 'Kolkata' },
        { latitude: 23.0225, longitude: 72.5714, address: 'Ahmedabad' },
        { latitude: 17.3850, longitude: 78.4867, address: 'Hyderabad' },
        { latitude: 18.5204, longitude: 73.8567, address: 'Pune' }
      ],
      'China': [
        { latitude: 39.9042, longitude: 116.4074, address: 'Beijing' },
        { latitude: 31.2304, longitude: 121.4737, address: 'Shanghai' },
        { latitude: 23.1291, longitude: 113.2644, address: 'Guangzhou' },
        { latitude: 22.3193, longitude: 114.1694, address: 'Shenzhen' },
        { latitude: 30.5728, longitude: 104.0668, address: 'Chengdu' },
        { latitude: 29.5630, longitude: 106.5516, address: 'Chongqing' }
      ],
      'United States': [
        { latitude: 40.7128, longitude: -74.0060, address: 'New York' },
        { latitude: 34.0522, longitude: -118.2437, address: 'Los Angeles' },
        { latitude: 41.8781, longitude: -87.6298, address: 'Chicago' },
        { latitude: 29.7604, longitude: -95.3698, address: 'Houston' },
        { latitude: 33.4484, longitude: -112.0740, address: 'Phoenix' },
        { latitude: 39.9526, longitude: -75.1652, address: 'Philadelphia' }
      ],
      'Japan': [
        { latitude: 35.6762, longitude: 139.6503, address: 'Tokyo' },
        { latitude: 34.6937, longitude: 135.5023, address: 'Osaka' },
        { latitude: 35.0116, longitude: 135.7681, address: 'Kyoto' },
        { latitude: 35.1815, longitude: 136.9066, address: 'Nagoya' }
      ],
      'Germany': [
        { latitude: 52.5200, longitude: 13.4050, address: 'Berlin' },
        { latitude: 48.1351, longitude: 11.5820, address: 'Munich' },
        { latitude: 50.1109, longitude: 8.6821, address: 'Frankfurt' },
        { latitude: 53.5511, longitude: 9.9937, address: 'Hamburg' }
      ],
      'Australia': [
        { latitude: -33.8688, longitude: 151.2093, address: 'Sydney' },
        { latitude: -37.8136, longitude: 144.9631, address: 'Melbourne' },
        { latitude: -27.4698, longitude: 153.0251, address: 'Brisbane' },
        { latitude: -31.9505, longitude: 115.8605, address: 'Perth' }
      ],
      'Brazil': [
        { latitude: -23.5505, longitude: -46.6333, address: 'São Paulo' },
        { latitude: -22.9068, longitude: -43.1729, address: 'Rio de Janeiro' },
        { latitude: -15.8267, longitude: -47.9218, address: 'Brasília' },
        { latitude: -19.8157, longitude: -43.9542, address: 'Belo Horizonte' }
      ],
      'Canada': [
        { latitude: 43.6532, longitude: -79.3832, address: 'Toronto' },
        { latitude: 45.5017, longitude: -73.5673, address: 'Montreal' },
        { latitude: 49.2827, longitude: -123.1207, address: 'Vancouver' },
        { latitude: 51.0447, longitude: -114.0719, address: 'Calgary' }
      ],
      'France': [
        { latitude: 48.8566, longitude: 2.3522, address: 'Paris' },
        { latitude: 43.7102, longitude: 7.2620, address: 'Nice' },
        { latitude: 43.2965, longitude: 5.3698, address: 'Marseille' },
        { latitude: 45.7640, longitude: 4.8357, address: 'Lyon' }
      ],
      'UK': [
        { latitude: 51.5074, longitude: -0.1278, address: 'London' },
        { latitude: 53.4808, longitude: -2.2426, address: 'Manchester' },
        { latitude: 55.9533, longitude: -3.1883, address: 'Edinburgh' },
        { latitude: 52.4862, longitude: -1.8904, address: 'Birmingham' }
      ]
    };
    return mockData[country] || [];
  };

  const handleSubmit = async () => {
    if (selectedRegion && selectedCountry) {
      setLoading(true);
      try {
        const coords = await fetchCoordinates(selectedRegion, selectedCountry);
        setCoordinates(coords);
      } catch (error) {
        console.error('Error fetching coordinates:', error);
      } finally {
        setLoading(false);
      }
    }
  };

  // Get the center coordinates for the map based on selected coordinates
  const getMapCenter = (): [number, number] => {
    if (coordinates.length === 0) return [20, 0];
    
    const avgLat = coordinates.reduce((sum, coord) => sum + coord.latitude, 0) / coordinates.length;
    const avgLng = coordinates.reduce((sum, coord) => sum + coord.longitude, 0) / coordinates.length;
    
    return [avgLat, avgLng];
  };

  const getMapZoom = (): number => {
    if (coordinates.length === 0) return 2;
    if (coordinates.length === 1) return 8;
    
    // Calculate zoom based on coordinate spread
    const latitudes = coordinates.map(coord => coord.latitude);
    const longitudes = coordinates.map(coord => coord.longitude);
    
    const latSpread = Math.max(...latitudes) - Math.min(...latitudes);
    const lngSpread = Math.max(...longitudes) - Math.min(...longitudes);
    const maxSpread = Math.max(latSpread, lngSpread);
    
    if (maxSpread < 1) return 8;
    if (maxSpread < 5) return 6;
    if (maxSpread < 10) return 5;
    if (maxSpread < 20) return 4;
    return 3;
  };

  return (
    <div className="region-city-map-container">
      <div className="dropdown-container">
        <select value={selectedRegion} onChange={handleRegionChange}>
          <option value="">Select Region</option>
          {regions.map((region) => (
            <option key={region} value={region}>
              {region}
            </option>
          ))}
        </select>
        
        <select 
          value={selectedCountry} 
          onChange={handleCountryChange} 
          disabled={!selectedRegion}
        >
          <option value="">Select Country</option>
          {countries.map((country) => (
            <option key={country} value={country}>
              {country}
            </option>
          ))}
        </select>
        
        <button 
          onClick={handleSubmit} 
          disabled={!selectedRegion || !selectedCountry || loading}
        >
          {loading ? 'Loading...' : 'Get Locations'}
        </button>
        
        {coordinates.length > 0 && (
          <div className="coordinate-info">
            Found {coordinates.length} location{coordinates.length > 1 ? 's' : ''} in {selectedCountry}
          </div>
        )}
      </div>
      
      <div className="map-container">
        <MapContainer 
          center={getMapCenter()} 
          zoom={getMapZoom()} 
          style={{ height: '100%', width: '100%' }}
          key={`${selectedRegion}-${selectedCountry}-${coordinates.length}`} // Force re-render on data change
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          {coordinates.map((coord, index) => (
            <Marker key={index} position={[coord.latitude, coord.longitude]}>
              <Popup>
                <div>
                  <strong>{coord.address || `Location ${index + 1}`}</strong><br />
                  <small>
                    Lat: {coord.latitude.toFixed(4)}<br />
                    Lng: {coord.longitude.toFixed(4)}
                  </small>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
};

export default RegionCityMap;
