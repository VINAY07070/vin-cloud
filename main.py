<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>VinOS</title>
    <link rel="icon" href="https://t4.ftcdn.net/jpg/03/33/10/19/360_F_333101957_kYiZiasjb6SXJWqYchZ36H5MuFFsKtfv.jpg">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=Dancing+Script:wght@700&family=Orbitron:wght@500&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #030303; --panel: #0e0e11; --text: #e5e5e5; --accent: #6366f1; --font-main: 'Outfit', sans-serif; --radius: 24px; --glow: 0 0 30px rgba(99, 102, 241, 0.15); --border: 1px solid rgba(255,255,255,0.08); --sig-color: rgba(255, 255, 255, 0.1); }
        [data-theme="cyberpunk"] { --bg: #05000a; --panel: #1a0b2e; --text: #ffccff; --accent: #d946ef; --font-main: 'Orbitron', sans-serif; --radius: 4px; --glow: 0 0 20px rgba(217, 70, 239, 0.4); --border: 1px solid rgba(217, 70, 239, 0.3); --sig-color: rgba(217, 70, 239, 0.2); }
        [data-theme="matrix"] { --bg: #000; --panel: #001100; --text: #00ff41; --accent: #008f11; --font-main: 'Share Tech Mono', monospace; --radius: 0px; --glow: 0 0 15px rgba(0, 255, 65, 0.2); --border: 1px solid rgba(0, 255, 65, 0.2); --sig-color: rgba(0, 255, 0, 0.1); }
        [data-theme="light"] { --bg: #f3f4f6; --panel: #ffffff; --text: #1f2937; --accent: #4f46e5; --font-main: 'Outfit', sans-serif; --radius: 20px; --glow: 0 20px 40px -5px rgba(0,0,0,0.1); --border: 1px solid rgba(0,0,0,0.05); --sig-color: rgba(0, 0, 0, 0.08); }
        body { background: var(--bg); color: var(--text); font-family: var(--font-main); overflow: hidden; transition: 0.5s; }
        .anim-header { animation: slideDown 0.8s forwards; transform: translateY(-100%); opacity: 0; }
        .anim-chat { animation: fadeIn 1s 0.5s forwards; opacity: 0; }
        .anim-input { animation: slideUp 0.8s 0.3s forwards; transform: translateY(100%); opacity: 0; }
        @keyframes slideDown { to { transform: translateY(0); opacity: 1; } } @keyframes slideUp { to { transform: translateY(0); opacity: 1; } } @keyframes fadeIn { to { opacity: 1; } }
        .vinay-sig { position: fixed; font-family: 'Dancing Script', cursive; color: var(--sig-color); pointer-events: none; z-index: 0; animation: floatSig 6s infinite; }
        @media (max-width: 768px) { .vinay-sig { top: 80px; right: 20px; font-size: 2.5rem; transform: rotate(-5deg); } }
        @media (min-width: 769px) { .vinay-sig { bottom: 30px; right: 40px; font-size: 4rem; transform: rotate(-10deg); } }
        @keyframes floatSig { 0%, 100% { transform: translateY(0) rotate(-5deg); } 50% { transform: translateY(-10px) rotate(-5deg); } }
        .input-glow-container { background: var(--panel); border: var(--border); border-radius: var(--radius); transition: 0.3s; }
        .input-glow-container:focus-within { box-shadow: var(--glow); border-color: var(--accent); transform: scale(1.01); }
        .msg-user { background: var(--accent); color: #fff; border-radius: 18px 18px 4px 18px; }
        .msg-ai { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 18px 18px 18px 4px; color: var(--text); }
        [data-theme="light"] .msg-ai { background: #fff; border-color: #eee; color: #333; }
        .action-btn { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: var(--text); padding: 8px 16px; border-radius: 99px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; transition: 0.2s; display: flex; align-items: center; gap: 6px; }
        [data-theme="light"] .action-btn { background: #fff; border-color: #eee; color: #555; }
        .action-btn:hover { background: var(--accent); color: white; border-color: var(--accent); transform: translateY(-1px); }
        #settingsMenu { transition: 0.3s; background: var(--panel); border-bottom: var(--border); } .hidden-menu { transform: translateY(-150%); }
        .wave-bar { width: 3px; background: var(--accent); animation: wave 0.5s infinite; height: 10px; } @keyframes wave { 0%, 100% { height: 10px; } 50% { height: 25px; } }
    </style>
</head>
<body class="h-screen flex flex-col relative" data-theme="stealth">
    <div class="vinay-sig">Vinay</div>
    <div class="h-16 backdrop-blur-md flex items-center justify-between px-5 sticky top-0 z-50 anim-header" style="border-bottom: var(--border)">
        <div class="flex items-center gap-3"><img src="https://t4.ftcdn.net/jpg/03/33/10/19/360_F_333101957_kYiZiasjb6SXJWqYchZ36H5MuFFsKtfv.jpg" class="w-8 h-8 rounded-full border border-white/20 shadow-lg"><div class="text-xl font-bold">Vin<span style="color: var(--accent)">OS</span></div><div id="aiSpeaking" class="flex gap-1 opacity-0 transition-opacity duration-300 ml-2"><div class="wave-bar" style="animation-delay: 0s"></div><div class="wave-bar" style="animation-delay: 0.1s"></div><div class="wave-bar" style="animation-delay: 0.2s"></div></div></div>
        <div class="flex gap-2"><button onclick="play('click'); clearHist()" class="action-btn">Clear</button><button onclick="play('click'); toggleMenu()" class="action-btn">Themes</button><a href="/logout" onclick="play('click')" class="action-btn" style="color: #ef4444; border-color: rgba(239,68,68,0.3)">Exit</a></div>
    </div>
    <div id="settingsMenu" class="absolute top-16 left-0 w-full p-5 z-40 hidden-menu shadow-2xl"><div class="flex justify-center gap-4 flex-wrap"><button onclick="setTheme('stealth')" class="px-5 py-3 rounded-xl border border-gray-700 bg-gray-900 text-white text-xs font-bold uppercase hover:scale-105 transition">Stealth</button><button onclick="setTheme('light')" class="px-5 py-3 rounded-xl border border-gray-200 bg-white text-black text-xs font-bold uppercase hover:scale-105 transition">Light</button><button onclick="setTheme('cyberpunk')" class="px-5 py-3 rounded-xl border border-fuchsia-500 bg-fuchsia-950 text-fuchsia-300 text-xs font-bold uppercase hover:scale-105 transition">Cyberpunk</button><button onclick="setTheme('matrix')" class="px-5 py-3 rounded-xl border border-green-500 bg-black text-green-400 text-xs font-bold uppercase hover:scale-105 transition font-mono">Matrix</button></div></div>
    <div id="chatFeed" class="flex-1 overflow-y-auto p-4 space-y-6 pb-32 scroll-smooth z-10 anim-chat"><div id="welcome" class="h-full flex flex-col items-center justify-center opacity-30 select-none"><div class="w-20 h-20 rounded-full flex items-center justify-center mb-4 animate-bounce overflow-hidden border border-white/10"><img src="https://t4.ftcdn.net/jpg/03/33/10/19/360_F_333101957_kYiZiasjb6SXJWqYchZ36H5MuFFsKtfv.jpg" class="w-full h-full object-cover opacity-80"></div><h1 class="text-3xl font-bold tracking-tight">System Online</h1><p class="text-xs mt-3 uppercase tracking-[0.3em]">Awaiting Input</p></div></div>
    <div class="fixed bottom-0 w-full p-4 pb-8 z-20 anim-input"><div class="max-w-3xl mx-auto flex items-end gap-2 p-2 input-glow-container"><button id="micBtn" onclick="toggleMic(); play('click')" class="p-4 rounded-xl text-zinc-500 hover:text-indigo-500 transition relative overflow-hidden"><div id="micPulse" class="absolute inset-0 bg-indigo-500/10 hidden animate-pulse"></div><svg class="w-5 h-5 relative z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg></button><textarea id="inp" rows="1" class="flex-1 bg-transparent placeholder-zinc-500 text-sm p-4 focus:outline-none resize-none max-h-32 transition-colors" style="color: var(--text)" placeholder="Enter command..."></textarea><button onclick="send()" class="p-4 rounded-xl text-white shadow-lg transition transform active:scale-90 hover:opacity-90" style="background-color: var(--accent); border-radius: var(--radius)"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7"></path></svg></button></div></div>
    <script>
        const sound = { play: (t) => { try { const ctx = new (window.AudioContext||window.webkitAudioContext)(); const osc = ctx.createOscillator(); const g = ctx.createGain(); osc.type = t==='click'?'sine':'triangle'; osc.frequency.setValueAtTime(t==='click'?800:600, ctx.currentTime); g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime+(t==='click'?0.1:0.15)); osc.connect(g); g.connect(ctx.destination); osc.start(); osc.stop(ctx.currentTime+0.2); } catch(e){} } };
        const play = (t) => sound.play(t);
        
        let rec = null, isL = false;
        try { const R = window.SpeechRecognition || window.webkitSpeechRecognition; if(R) { rec = new R(); rec.continuous=false; rec.lang='en-US'; rec.onstart=()=>{isL=true; document.getElementById('micPulse').classList.remove('hidden'); document.getElementById('inp').placeholder="Listening...";}; rec.onend=()=>{isL=false; document.getElementById('micPulse').classList.add('hidden'); document.getElementById('inp').placeholder="Enter command...";}; rec.onresult=(e)=>{document.getElementById('inp').value=e.results[0][0].transcript; send(true);}; } } catch(e){}
        function toggleMic() { if(!rec) return alert("No Voice Support"); isL ? rec.stop() : rec.start(); }

        async function playVoice(txt) {
            document.getElementById('aiSpeaking').classList.remove('opacity-0');
            try { const res = await fetch('/api/tts', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({text:txt})}); const b = await res.blob(); const a = new Audio(URL.createObjectURL(b)); a.onended=()=>{document.getElementById('aiSpeaking').classList.add('opacity-0');}; a.play(); } catch(e){document.getElementById('aiSpeaking').classList.add('opacity-0');}
        }

        let hist = [];
        try { const s = localStorage.getItem('vin_v12'); if(s) { hist = JSON.parse(s); if(hist.length) { document.getElementById('welcome').style.display='none'; hist.forEach(m=>addMsg(m.role,m.content,false)); } } } catch(e){}
        function toggleMenu() { document.getElementById('settingsMenu').classList.toggle('hidden-menu'); }
        function setTheme(t) { document.body.setAttribute('data-theme', t); toggleMenu(); }
        function clearHist() { if(confirm("Clear Memory?")) { localStorage.removeItem('vin_v12'); location.reload(); } }
        function saveHist(r,c) { hist.push({role:r, content:c}); localStorage.setItem('vin_v12', JSON.stringify(hist)); }

        async function send(voice=false) {
            const inp = document.getElementById('inp'); const txt = inp.value.trim(); if(!txt) return;
            play('send'); document.getElementById('welcome').style.display='none'; inp.value=''; inp.style.height='auto';
            addMsg('user', txt); saveHist('user', txt);
            if(voice) document.getElementById('aiSpeaking').classList.remove('opacity-0');
            
            try {
                // BUG FIX: We send the history separately from the new message
                const res = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message:txt, history: hist.slice(0, -1)})});
                const d = await res.json();
                setTimeout(() => { play('click'); addMsg('ai', d.response); saveHist('assistant', d.response); if(voice) playVoice(d.response); else document.getElementById('aiSpeaking').classList.add('opacity-0'); }, 200);
            } catch(e) { addMsg('ai', "SYSTEM ERROR"); document.getElementById('aiSpeaking').classList.add('opacity-0'); }
        }

        function addMsg(role, txt, anim=true) {
            const d = document.createElement('div'); const u = role==='user'; d.className = `flex ${u?'justify-end':'justify-start'} mb-4`;
            const c = document.body.getAttribute('data-theme')==='light'?'text-black/30 hover:text-black':'text-white/30 hover:text-white';
            const btn = !u ? `<button onclick="playVoice(this.parentNode.innerText)" class="absolute -right-8 top-2 ${c} transition"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"></path></svg></button>` : '';
            d.innerHTML = `<div class="flex flex-col ${u?'items-end':'items-start'} max-w-[85%] relative group ${anim?'msg-enter':''}"><div class="p-4 text-[15px] leading-relaxed ${u?'msg-user':'msg-ai'}">${marked.parse(txt)}</div>${btn}</div>`;
            document.getElementById('chatFeed').appendChild(d); window.scrollTo(0, document.body.scrollHeight);
        }
        document.getElementById('inp').addEventListener('keydown', (e)=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}});
    </script>
</body>
</html>
