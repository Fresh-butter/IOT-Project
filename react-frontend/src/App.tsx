import { CssBaseline, Container, ThemeProvider, createTheme } from '@mui/material';
import './App.css';
import Header from './components/Header';
import RoutesList from './components/RoutesList';

// Create a theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Header />
      <Container maxWidth="xl">
        <RoutesList />
      </Container>
    </ThemeProvider>
  );
}

export default App;