# Trading System Dashboard

A modern, responsive dashboard for managing trading operations, user accounts, and system monitoring.

## Features

- User Management
- Performance Metrics
- Risk Management
- System Monitoring
- Real-time Updates

## Deployment

### Prerequisites

- Node.js 18 or higher
- npm or yarn
- Netlify account

### Local Development

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm start
```

3. Build for production:
```bash
npm run build
```

### Deploying to Netlify

1. Push your code to GitHub

2. Connect to Netlify:
   - Go to [Netlify](https://app.netlify.com)
   - Click "New site from Git"
   - Select your repository
   - Configure build settings:
     - Build command: `npm run build`
     - Publish directory: `build`
   - Click "Deploy site"

3. Configure environment variables in Netlify:
   - Go to Site settings > Build & deploy > Environment
   - Add the following variables:
     ```
     REACT_APP_API_URL=your_api_url
     REACT_APP_WS_URL=your_websocket_url
     ```

4. Enable HTTPS:
   - Go to Site settings > Domain management
   - Click "Verify DNS configuration"
   - Follow the instructions to set up your custom domain

## Environment Variables

Create a `.env` file in the root directory:

```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT 