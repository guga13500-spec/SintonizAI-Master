// Filename: server.js
// SintonizAI "Master Omni-Agent"
// Final Automation Version for Gustavo

require('dotenv').config();
const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const Database = require('better-sqlite3');
const axios = require('axios');
const path = require('path');

const app = express();
const db = new Database('sintonizai_master.db');

// --- Middleware ---
app.use(helmet({ contentSecurityPolicy: false })); // Permite carregar recursos externos
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public'))); // Servir arquivos estáticos

// --- DB Schema ---
db.exec(`
  CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, email TEXT UNIQUE, password_hash TEXT);
  CREATE TABLE IF NOT EXISTS agents (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, model TEXT, api_key TEXT);
  CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT, command TEXT, status TEXT DEFAULT 'pending', result TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP);
`);

const JWT_SECRET = process.env.JWT_SECRET || 'guga-2026-secret';

// --- Multi-Model Logic ---
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

async function callAI(model, prompt, key) {
    // Se não houver chave e for o modo auto, usa o Token do Servidor (GitHub Models)
    let activeKey = key;
    let activeModel = model;
    let endpoint = '';
    let headers = {};
    let data = {};

    if (!key && GITHUB_TOKEN) {
        activeKey = GITHUB_TOKEN;
        activeModel = 'gpt-4o'; // Padrão potente do GitHub Models
    }

    if (!activeKey) return "Configure sua chave de API ou use o modo Master.";

    try {
        if (activeModel === 'gemini') {
            endpoint = `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${activeKey}`;
            data = { contents: [{ parts: [{ text: prompt }] }] };
            const res = await axios.post(endpoint, data);
            return res.data.candidates[0].content.parts[0].text;
        }

        // GitHub Models (OpenAI Compatible)
        if (activeModel === 'gpt-4o' || activeModel === 'master') {
            endpoint = 'https://models.inference.ai.azure.com/chat/completions';
            headers = { 'Authorization': `Bearer ${activeKey}`, 'Content-Type': 'application/json' };
            data = { 
                model: "gpt-4o", 
                messages: [{ role: "user", content: prompt }],
                temperature: 0.7
            };
            const res = await axios.post(endpoint, data, { headers });
            return res.data.choices[0].message.content;
        }

        if (activeModel === 'groq') {
            endpoint = 'https://api.groq.com/openai/v1/chat/completions';
            headers = { 'Authorization': `Bearer ${activeKey}` };
            data = { model: "llama3-70b-8192", messages: [{ role: "user", content: prompt }] };
            const res = await axios.post(endpoint, data, { headers });
            return res.data.choices[0].message.content;
        }
        
        return "Modelo " + activeModel + " não suportado ou em manutenção.";
    } catch (e) { 
        console.error("Erro na IA:", e.response?.data || e.message);
        return "Erro no Agente " + activeModel + ": " + (e.response?.data?.error?.message || e.message); 
    }
}

// --- Endpoints ---
app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'index.html')));

app.post('/api/auth/register', async (req, res) => {
    const { username, email, password } = req.body;
    const hash = await bcrypt.hash(password, 10);
    try {
        db.prepare('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)').run(username, email.toLowerCase(), hash);
        res.json({ success: true });
    } catch (e) { res.status(400).json({ error: "Email já existe." }); }
});

app.post('/api/auth/login', async (req, res) => {
    const { email, password } = req.body;
    const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email.toLowerCase());
    if (user && await bcrypt.compare(password, user.password_hash)) {
        const token = jwt.sign({ id: user.id, username: user.username }, JWT_SECRET);
        res.json({ success: true, token, username: user.username });
    } else { res.status(401).json({ error: "Inválido." }); }
});

app.post('/api/agent/chat', async (req, res) => {
    const { message, model, apiKey } = req.body;
    const response = await callAI(model || 'gemini', message, apiKey);
    res.json({ success: true, response });
});

app.post('/api/tasks/create', (req, res) => {
    const { userId, type, command } = req.body;
    db.prepare('INSERT INTO tasks (user_id, type, command) VALUES (?, ?, ?)').run(userId, type, command);
    res.json({ success: true, message: "Agente em campo. Te aviso quando terminar!" });
});

app.get('/api/tasks/list', (req, res) => {
    const tasks = db.prepare('SELECT * FROM tasks ORDER BY created_at DESC').all();
    res.json({ success: true, tasks });
});

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => console.log(`SintonizAI Master Vivo na Porta ${PORT}`));
