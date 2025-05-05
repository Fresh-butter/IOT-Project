import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardActionArea,
  CardContent, 
  Typography, 
  Chip, 
  CircularProgress, 
  Alert,
  Paper,
  Divider
} from '@mui/material';
import { fetchRoutes, Route } from '../services/api';
import RouteMap from './RouteMap';

const RoutesList: React.FC = () => {
  const [routes, setRoutes] = useState<Route[]>([]);
  const [selectedRoute, setSelectedRoute] = useState<Route | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadRoutes = async () => {
      try {
        setLoading(true);
        const data = await fetchRoutes();
        setRoutes(data);
        setError(null);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('Failed to fetch routes');
        }
      } finally {
        setLoading(false);
      }
    };

    loadRoutes();
  }, []);

  const handleRouteClick = (route: Route) => {
    setSelectedRoute(route);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ my: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ py: 2 }}>
      <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
        
        {/* Left column: Routes list */}
        <Box sx={{ width: { xs: '100%', md: '41.666%' } }}>
          <Typography variant="h5" component="h2" gutterBottom>
            Available Routes
          </Typography>
          
          <Box sx={{ maxHeight: 'calc(100vh - 220px)', overflowY: 'auto', pr: 1 }}>
            {routes.length === 0 ? (
              <Alert severity="info">No routes available</Alert>
            ) : (
              routes.map((route) => (
                <Card 
                  key={route._id}
                  sx={{ 
                    mb: 2, 
                    border: selectedRoute?._id === route._id ? '2px solid #1976d2' : '1px solid #e0e0e0',
                    transition: 'all 0.2s',
                    '&:hover': {
                      boxShadow: 3
                    }
                  }}
                >
                  <CardActionArea onClick={() => handleRouteClick(route)}>
                    <CardContent>
                      <Typography variant="h6">{route.route_name}</Typography>
                      <Typography color="text.secondary" gutterBottom>ID: {route.route_id}</Typography>
                      
                      <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        <Chip 
                          label={`${route.checkpoints.length} checkpoints`}
                          size="small"
                          sx={{ mr: 1 }}
                        />
                        
                        {route.assigned_train_id && (
                          <Chip 
                            label={`Train: ${route.assigned_train_id}`}
                            color="primary"
                            size="small"
                          />
                        )}
                      </Box>
                      
                      {route.start_time && (
                        <Typography variant="body2" sx={{ mt: 1 }}>
                          Starts: {new Date(route.start_time).toLocaleString()}
                        </Typography>
                      )}
                    </CardContent>
                  </CardActionArea>
                </Card>
              ))
            )}
          </Box>
        </Box>
        
        {/* Right column: Map and details */}
        <Box sx={{ width: { xs: '100%', md: '58.333%' } }}>
          <Typography variant="h5" component="h2" gutterBottom>
            Route Map
          </Typography>
          
          <RouteMap selectedRoute={selectedRoute} />
          
          {selectedRoute && (
            <Paper elevation={2} sx={{ mt: 2, p: 2 }}>
              <Typography variant="h6" gutterBottom>Route Details</Typography>
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                {/* Left details column */}
                <Box sx={{ flexBasis: { xs: '100%', sm: 'calc(50% - 1rem)' } }}>
                  <Typography variant="body2">
                    <strong>Name:</strong> {selectedRoute.route_name}
                  </Typography>
                  <Typography variant="body2">
                    <strong>ID:</strong> {selectedRoute.route_id}
                  </Typography>
                  {selectedRoute.assigned_train_id && (
                    <Typography variant="body2">
                      <strong>Assigned Train:</strong> {selectedRoute.assigned_train_id}
                    </Typography>
                  )}
                </Box>
                
                {/* Right details column */}
                <Box sx={{ flexBasis: { xs: '100%', sm: 'calc(50% - 1rem)' } }}>
                  {selectedRoute.start_time && (
                    <Typography variant="body2">
                      <strong>Start Time:</strong> {new Date(selectedRoute.start_time).toLocaleString()}
                    </Typography>
                  )}
                  <Typography variant="body2">
                    <strong>Checkpoints:</strong> {selectedRoute.checkpoints.length}
                  </Typography>
                </Box>
                
                {/* Full width bottom section */}
                <Box sx={{ width: '100%' }}>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="subtitle2">Checkpoint Names:</Typography>
                  <Box sx={{ mt: 1 }}>
                    {selectedRoute.checkpoints.map((checkpoint, index) => (
                      <Chip 
                        key={index}
                        label={checkpoint.name || `Checkpoint ${index + 1}`}
                        size="small"
                        sx={{ mr: 1, mb: 1 }}
                      />
                    ))}
                  </Box>
                </Box>
              </Box>
            </Paper>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default RoutesList;