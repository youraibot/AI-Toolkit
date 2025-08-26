import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import TrainingDashboard from './components/TrainingDashboard';
import JobAnalytics from './components/JobAnalytics';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/models" element={<Dashboard />} />
            <Route path="/training" element={<TrainingDashboard />} />
            <Route path="/analytics" element={<JobAnalytics />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
