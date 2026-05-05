# Guitar Tablature Generator - Frontend

A React web application for uploading guitar audio and generating ASCII tablature with note positions.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start the Development Server

```bash
npm run dev
```

This will open `http://localhost:5173` in your browser automatically.

### 3. Make Sure Backend is Running

In another terminal, run the FastAPI backend:

```bash
cd ..
python main.py
```

The backend should be running on `http://localhost:8000`

## 📖 How It Works

### The 3-Step Process:

1. **Upload** → Select an audio file (WAV, MP3, etc.)
2. **Choose Position** → Select where to play the first note
3. **View Result** → Get the complete tablature and note sequence

### Key Concepts for React Beginners:

**State** (`useState`)
- `file` - The audio file you selected
- `step` - Tracks which step you're on ('upload', 'select', 'result')
- `sessionId` - A unique ID for this processing session (backend needs this)
- `options` - The list of string/fret choices for the first note
- `result` - The final tablature and note data

**Flow**:
```
Upload File 
    ↓
Backend detects notes → returns options
    ↓
User selects starting position
    ↓
Backend generates tablature → displays result
```

### Important Files:

- `src/App.jsx` - Main component (all logic is here)
- `src/App.css` - Styling
- `index.html` - HTML template
- `vite.config.js` - Build configuration

## 🔧 Customization

### Change Backend URL

In `src/App.jsx`, line 16:
```javascript
const API_BASE = 'http://localhost:8000'; // Change this
```

### Styling

All CSS is in `src/App.css`. Modify colors, fonts, spacing here.

### Add New Features

To add something like:
- Audio playback preview
- Frequency chart visualization
- Export as image

You would:
1. Add new state variables with `useState()`
2. Create new components or sections in JSX
3. Add styling in `App.css`
4. Make API calls with `axios` as needed

## 📦 Build for Production

```bash
npm run build
```

This creates an optimized `dist/` folder ready to deploy.

## 🐛 Troubleshooting

**"Cannot connect to backend"**
- Make sure `main.py` is running on `http://localhost:8000`
- Check CORS is enabled in `main.py`

**"No notes detected"**
- Try a clearer audio file
- Some audio formats may not work well

**"npm: command not found"**
- Install Node.js from https://nodejs.org

## 📚 Learning Resources

- React Basics: https://react.dev
- Using State: https://react.dev/reference/react/useState
- HTTP Requests with Axios: https://axios-http.com
- Vite Documentation: https://vitejs.dev
