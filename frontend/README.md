# Compliance Dashboard Frontend

React-based dashboard for the Intelligent Compliance and Risk Agent system.

## Features

- **Real-time Alert Dashboard**: Monitor compliance violations with filtering, sorting, and pagination
- **Interactive Compliance Analyzer**: Analyze business communications for potential violations
- **Metrics Visualization**: Charts and KPIs showing system performance and business impact
- **Mobile-Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Material-UI Components**: Modern, accessible user interface

## Technology Stack

- **React 18** with TypeScript
- **Material-UI (MUI)** for components and theming
- **React Query** for server state management
- **Zustand** for client state management
- **MUI X Charts** for data visualization
- **React Router** for navigation

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API running (see main project README)

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm start
```

Runs the app in development mode on [http://localhost:3000](http://localhost:3000).

### Building for Production

```bash
npm run build
```

Builds the app for production to the `build` folder.

### Testing

```bash
npm test
```

Runs the test suite.

## Project Structure

```
src/
├── components/          # React components
│   ├── Dashboard.tsx    # Main dashboard page
│   ├── ComplianceAnalyzer.tsx  # Interactive analyzer
│   ├── AlertsTable.tsx  # Alert management table
│   ├── MetricsCards.tsx # KPI cards
│   ├── MetricsCharts.tsx # Data visualization
│   ├── AlertFilters.tsx # Filter controls
│   └── Navigation.tsx   # App navigation
├── services/           # API service layer
│   └── api.ts         # API client and mock data
├── store/             # State management
│   └── useStore.ts    # Zustand store
├── App.tsx            # Main app component
└── index.tsx          # App entry point
```

## Key Features

### Real-time Monitoring
- Automatic refresh every 5 seconds
- Live alert updates
- Performance metrics tracking

### Interactive Analysis
- Text input for immediate compliance analysis
- Demo scenarios for testing
- Detailed violation explanations with regulatory citations

### Mobile Optimization
- Responsive design for all screen sizes
- Touch-friendly interface
- Optimized table layouts for mobile

### Data Visualization
- Risk level distribution charts
- Performance vs target metrics
- Weekly activity trends
- Business impact summaries

## API Integration

The frontend integrates with the backend API for:
- Fetching real-time alerts
- Retrieving system metrics
- Analyzing communication content
- Updating alert statuses

Mock data is provided for demo purposes when the API is unavailable.

## Configuration

Environment variables:
- `REACT_APP_API_URL`: Backend API base URL (defaults to `/api`)

## Demo Scenarios

The analyzer includes pre-configured demo scenarios:
1. **Earnings Manipulation**: Critical risk detection
2. **Insider Trading**: High risk detection  
3. **Legitimate Business**: Low risk baseline

These scenarios demonstrate the AI's ability to distinguish between compliant and non-compliant communications.