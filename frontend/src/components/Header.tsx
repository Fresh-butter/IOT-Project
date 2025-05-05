import React from 'react';
import { AppBar, Toolbar, Typography, Box } from '@mui/material';
import DirectionsRailwayIcon from '@mui/icons-material/DirectionsRailway';

const Header: React.FC = () => {
  return (
    <AppBar position="static" sx={{ mb: 3 }}>
      <Toolbar>
        <DirectionsRailwayIcon sx={{ mr: 2 }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Train Collision Avoidance System
        </Typography>
        <Box>
          <Typography variant="subtitle1">
            Routes Explorer
          </Typography>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;