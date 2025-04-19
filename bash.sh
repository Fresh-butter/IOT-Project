#!/bin/bash

# Navigate to the react-frontend directory
cd react-frontend

# Create the base structure
mkdir -p src/components
mkdir -p src/pages
mkdir -p src/api
mkdir -p src/utils
mkdir -p src/styles
mkdir -p public

# Create components for reusable UI elements
touch src/components/Navbar.jsx
touch src/components/Footer.jsx
touch src/components/TrainList.jsx
touch src/components/RouteList.jsx
touch src/components/AlertList.jsx
touch src/components/LogList.jsx

# Create pages for different sections of the app
touch src/pages/Dashboard.jsx
touch src/pages/ApiDocs.jsx
touch src/pages/Trains.jsx
touch src/pages/Routes.jsx
touch src/pages/Alerts.jsx
touch src/pages/Logs.jsx
touch src/pages/Analytics.jsx

# Create API utility files for interacting with the backend
touch src/api/trains.js
touch src/api/routes.js
touch src/api/alerts.js
touch src/api/logs.js
touch src/api/analytics.js

# Create utility files for shared logic
touch src/utils/request.js
touch src/utils/helpers.js

# Create stylesheets
touch src/styles/global.css
touch src/styles/navbar.css
touch src/styles/footer.css

# Create the main entry files
touch src/App.jsx
touch src/main.jsx
touch src/index.css

# Create a public folder for static assets
touch public/index.html
touch public/favicon.ico

# Print success message
echo "React frontend file structure created successfully!"
