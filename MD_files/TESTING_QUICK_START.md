# Quick Start: Complete AI Integration Testing

## Prerequisites

- Python 3.8+ with backend dependencies installed
- Node.js with React frontend running
- Trained ML model at `ML/models/data_iter100000/pawn_outcome_model.joblib` (optional, dummy evaluator available)

---

## Step 1: Start the Backend Server

```bash
cd Game_Sim
python -m uvicorn backend.server:app --reload
```

Expected output:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

---

## Step 2: Start the Frontend Development Server

```bash
cd Game_Sim/web_app
npm install  # if needed
npm run dev
```

Expected output:

```
  VITE v5.x.x  ready in 123 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

---

## Step 3: Open in Browser

Navigate to: **http://localhost:5173**

---

## Step 4: Test Game Creation with AI

### Without AI Model (Dummy Evaluator)

1. **Click "New Game"** on home page
2. **Keep default settings** or customize as desired
3. **Scroll to "AI Configuration"** section
4. **Click "🚀 Initialize AI"** (no model needed)
   - This sets up dummy evaluator
   - Should show: "AI initialized successfully!" ✓
5. **Click "Start Game"** button

### With Trained Model

If you have `pawn_outcome_model.joblib`:

1. Follow steps 1-3 above
2. **Select model** from "Select Model" dropdown (if available)
3. **Choose strategy**: greedy, explore, epsilon-greedy, or random
4. **Adjust parameters** if needed (temperature, epsilon)
5. **Click "🚀 Initialize AI"**
   - Should show: "AI initialized successfully!" ✓
6. **Click "Start Game"**

---

## Step 5: Play Game with AI

Once in the game:

### Without AI Panel (AI Disabled)

- Actions show as normal
- No win probability badges
- Click "🤖 AI Disabled" button to enable

### With AI Panel (AI Enabled)

**Right panel shows:**

1. **AI Assistant Panel** (purple gradient)
   - Top recommendation with % win probability
   - Clickable "✓ Use This Move" button
   - "▼ Show All Options" to expand detailed rankings

2. **Action Buttons** with badges:

   ```
   [move A: 75%]  [move B: 42%]  [move C: 88%]
   ```

3. **AI Toggle Button**:
   - Click to switch between "🤖 AI Enabled" and "🚫 AI Disabled"

### Interacting with AI

**Option 1: Auto-play AI moves**

```
1. Click "✓ Use This Move" in AI Panel
2. Game automatically plays suggested move
3. AI re-evaluates for next turn
```

**Option 2: Manual move selection**

```
1. See win probabilities on action buttons
2. Click any action button to play
3. AI Panel updates for next state
```

**Option 3: Analyze moves**

```
1. Click "▼ Show All Options" to expand
2. See all moves ranked 1-N with probabilities
3. Make informed decision
```

---

## Step 6: Switch AI Strategy (During Game)

1. **Right-click on strategy** in AI Panel (if available)
   - OR use settings before starting game

2. **Game restarts evaluation** with new strategy

3. **Observe differences:**
   - Greedy: Always max probability
   - Explore: More random/exploratory
   - Epsilon-Greedy: Mixed approach
   - Random: Baseline for comparison

---

## Step 7: Verify Integration Points

### Frontend → Backend Communication

**Check Network tab (F12):**

```
POST /ai/status          ✓ 200
GET  /ai/models/available ✓ 200
GET  /ai/strategies/available ✓ 200
POST /ai/init            ✓ 200
POST /ai/suggest         ✓ 200
POST /ai/evaluate        ✓ 200
POST /start              ✓ 200
POST /action             ✓ 200
```

**Check Console for errors:**

- If red errors appear, check backend logs
- If API timeouts, verify server is running

---

## Testing Checklist

### Pre-Game Setup

- [ ] Navigate to home page
- [ ] Game configuration loads
- [ ] AI Settings section visible
- [ ] Model dropdown populated (or shows "no models")
- [ ] Strategy buttons clickable
- [ ] "Initialize AI" button works
- [ ] Success/error messages appear

### During Gameplay

- [ ] Action buttons display correctly
- [ ] Win probability badges appear (if AI enabled)
- [ ] AI Panel visible on right
- [ ] Top recommendation shows percentage
- [ ] "Use This Move" button clickable
- [ ] "Show All Options" expands/collapses
- [ ] AI toggle button switches state
- [ ] Colors change for different probabilities

### AI Interactions

- [ ] Click "Use This Move" → game plays move
- [ ] Click action button → AI updates
- [ ] Toggle AI on/off → panel appears/disappears
- [ ] Refresh button → re-evaluates current state
- [ ] Strategy changes → model re-evaluates

### Error Handling

- [ ] Try without model → dummy evaluator works
- [ ] Try with invalid model path → error shown
- [ ] Disconnect backend → error shown gracefully
- [ ] Refresh page → AI state preserved (localStorage)

---

## Common Test Scenarios

### Scenario 1: Total Beginner

```
1. Open app
2. Click New Game (use defaults)
3. Leave AI disabled
4. Play a few moves manually
5. Click "AI Enabled" button
6. Observe AI suggestions
7. Click suggested moves to see AI play
```

### Scenario 2: Strategy Comparison

```
1. Start game with Greedy strategy
2. Play a few moves, observe win probabilities
3. Mid-game, try switching to Epsilon-Greedy
4. Compare recommendations
5. Switch to Explore
6. Observe differences
```

### Scenario 3: Analysis Mode

```
1. Start game with any strategy
2. For each turn:
   a. Click "Show All Options"
   b. Study all ranked moves
   c. Understand why AI prefers certain moves
   d. Play any move (AI or manual)
3. Continue until win/lose
```

### Scenario 4: No Model (Fallback)

```
1. Start game without selecting model
2. Click "Initialize AI" (should still work)
3. Should use dummy evaluator
4. All moves should have similar/equal probabilities
5. Should still work correctly
```

---

## Performance Observations

### Expected Timings

- **First AI init**: 1-2 seconds (model loading)
- **First suggestion**: 100-300ms (first inference + setup)
- **Subsequent suggestions**: 50-100ms (cached)
- **Strategy switch**: ~300ms (re-evaluation)
- **UI response**: <50ms (local updates)

### Network Calls

- **Game start**: 1 POST (/start)
- **Each turn**: 1 POST (/action) + optional AI calls
- **AI enable**: 3 GETs (status, models, strategies)
- **AI init**: 1 POST (/ai/init)
- **Each AI suggestion**: 1 POST (/ai/evaluate)

---

## Debugging

### Enable Browser DevTools

**F12 → Console tab for messages:**

```javascript
// Check API responses
await fetch("/ai/status")
  .then((r) => r.json())
  .then(console.log);

// Check game state
localStorage.getItem("game_state");

// Check AI enabled
localStorage.getItem("ai_enabled");
```

**F12 → Network tab for requests:**

- Filter by "Fetch/XHR"
- See all API calls and responses
- Check status codes and response bodies

### Backend Logs

**Terminal running uvicorn should show:**

```
INFO:     127.0.0.1:60000 - "POST /start HTTP/1.1" 200
INFO:     127.0.0.1:60001 - "POST /action HTTP/1.1" 200
INFO:     127.0.0.1:60002 - "POST /ai/init HTTP/1.1" 200
INFO:     127.0.0.1:60003 - "POST /ai/evaluate HTTP/1.1" 200
```

---

## Stopping the Servers

### Stop Backend

```bash
# Terminal running uvicorn
Ctrl+C
```

### Stop Frontend

```bash
# Terminal running npm dev
Ctrl+C
```

---

## Next: Production Deployment

When ready to deploy:

1. Build frontend for production:

   ```bash
   cd web_app
   npm run build
   ```

2. Update API_BASE_URL in `api.js` for production server

3. Deploy backend to production server

4. Serve frontend static files

See [Deployment Guide](./DEPLOYMENT.md) for details.

---

## Troubleshooting

### Issue: Frontend can't connect to backend

**Solution:**

1. Ensure backend is running: `python -m uvicorn backend.server:app --reload`
2. Check VITE_API_BASE_URL in `.env` or `api.js`
3. Verify CORS is enabled in backend (should be)

### Issue: AI suggestions very slow

**Solution:**

1. Check if backend is processing (CPU usage)
2. Verify model exists and is loaded correctly
3. Try dummy evaluator first
4. Check backend logs for errors

### Issue: Model not found

**Solution:**

1. Verify path: `ML/models/data_iter100000/pawn_outcome_model.joblib`
2. Run training: `python ML/ML_model.py`
3. Check file permissions

### Issue: Win probability badges not showing

**Solution:**

1. Check if AI is enabled (green toggle)
2. Wait for "Analyzing..." to complete
3. Click "🔄 Refresh" button
4. Check browser console for errors

---

## Contact & Support

If issues persist:

1. Check the documentation files
2. Review backend logs
3. Check browser console (F12)
4. Verify all prerequisites are installed
