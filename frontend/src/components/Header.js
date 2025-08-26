import React from 'react';
import { Link } from 'react-router-dom';

function Header() {
    return (
        <header className="App-header">
            <div className="header-content">
                <Link to="/" className="logo"><h1>AI Toolkit</h1></Link>
                <nav>
                    <Link to="/models">Models</Link>
                    <Link to="/training">Training</Link>
                    <Link to="/analytics">Analytics</Link>
                </nav>
            </div>
        </header>
    );
}

export default Header;
