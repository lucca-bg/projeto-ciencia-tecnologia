# Step-by-Step Setup Guide for Beginners

## Prerequisites

1. **Node.js** - Download from https://nodejs.org (choose LTS version)
   - This includes `npm` (Node Package Manager - like Python pip)
   - Verify installation: open terminal and type `node --version`

2. **Python Backend** - Should already be running from your music scripts

## Setup Instructions

### Step 1: Navigate to Frontend Folder

```bash
cd "c:\Users\lucca\Desktop\Feevale\Projeto - Ciência e Tecnologia\frontend"
```

### Step 2: Install Dependencies

```bash
npm install
```

This downloads all the libraries the frontend needs (React, Axios, etc). Takes 1-2 minutes.

### Step 3: Start Backend (if not already running)

Open a new PowerShell window in the project folder:

```bash
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 4: Start Frontend

In another PowerShell window, still in the frontend folder:

```bash
npm run dev
```

You should see:
```
  ➜  Local:   http://localhost:5173/
```

Your browser will automatically open. If not, go to `http://localhost:5173`

## What Happens When You Upload

1. **Browser** sends audio file to backend
2. **Backend** (Python) detects notes using librosa
3. **Backend** sends back options for first note position
4. **Browser** shows options as radio buttons
5. You select one
6. **Browser** sends selection back to backend
7. **Backend** generates tablature based on your choice
8. **Browser** displays final result

## Understanding the Code

### App.jsx Structure

```jsx
// 1. Import libraries
import { useState } from 'react';  // For state management
import axios from 'axios';         // For HTTP requests

// 2. Define component
function App() {
  // 3. Create state variables
  const [file, setFile] = useState(null);
  
  // 4. Define functions that handle actions
  const handleUpload = async () => {
    // Send file to backend
  };
  
  // 5. Return JSX (HTML-like syntax)
  return (
    <div>
      {/* This is JSX - looks like HTML but it's JavaScript */}
    </div>
  );
}
```

### Key Concepts

**useState** - Remembers data between renders
```javascript
const [count, setCount] = useState(0);  // count is 0, setCount updates it
```

**async/await** - Waits for backend response
```javascript
const response = await axios.post(...);  // Wait for response
const data = response.data;              // Then use the data
```

**HTTP Requests** - Talking to backend
```javascript
axios.post(url, data)   // Send POST request
axios.get(url)          // Send GET request
```

## Common Tasks

### Change the API URL

If backend is on a different machine, edit `App.jsx` line 16:

```javascript
const API_BASE = 'http://192.168.x.x:8000';  // Your machine's IP
```

### Style the App

All colors, fonts, sizes are in `App.css`. Example:

```css
/* Change button background color */
.btn-primary {
  background: blue;  /* Change this */
}
```

### Add a New Field to Display

Add to JSX:
```jsx
<p>Detected Notes: {result.sequence.length}</p>
```

Add to CSS:
```css
p {
  color: #333;
  font-size: 16px;
}
```

## Troubleshooting

### "npm: command not found"
- Node.js not installed properly
- Restart terminal after installing Node

### "Cannot GET /"
- Frontend not running
- Run `npm run dev` again

### "Failed to fetch" or "Cannot connect"
- Backend not running
- Open new terminal and run `python main.py`
- Verify it says "Uvicorn running on http://127.0.0.1:8000"

### Port already in use
- Change port in `vite.config.js`:
  ```javascript
  server: {
    port: 5174,  // Change to this
  }
  ```

### Browser not opening automatically
- Manually go to `http://localhost:5173`

## Next Steps

1. **Test it** - Upload an audio file and see if it works
2. **Customize** - Change colors, add your logo, modify layout
3. **Deploy** - Put frontend on web server (Netlify, Vercel)
4. **Deploy Backend** - Put Python backend on cloud (Heroku, Railway)

## Resources

- React: https://react.dev/learn
- Axios: https://axios-http.com/docs/intro
- CSS: https://developer.mozilla.org/en-US/docs/Learn/CSS
- JavaScript: https://developer.mozilla.org/en-US/docs/Learn/JavaScript

Good luck! Ask if you get stuck. 🎸
