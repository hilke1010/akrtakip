if not st.session_state['splash_shown']:
    # Giriş Ekranı CSS
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@900&family=Rajdhani:wght@700&display=swap');
        
        .splash-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: #000;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 999999;
        }
        
        /* Animated Background Waves */
        .splash-container::before {
            content: '';
            position: absolute;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 30% 50%, rgba(0, 198, 255, 0.15), transparent 50%),
                        radial-gradient(circle at 70% 50%, rgba(255, 0, 150, 0.15), transparent 50%);
            animation: wave 8s ease-in-out infinite;
        }
        
        @keyframes wave {
            0%, 100% { transform: translate(-25%, -25%) rotate(0deg); }
            50% { transform: translate(-30%, -30%) rotate(180deg); }
        }
        
        /* 3D Rotating Cube */
        .cube-container {
            position: absolute;
            width: 200px;
            height: 200px;
            perspective: 1000px;
            animation: float 6s ease-in-out infinite;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-30px); }
        }
        
        .cube {
            width: 100%;
            height: 100%;
            position: relative;
            transform-style: preserve-3d;
            animation: rotateCube 10s infinite linear;
        }
        
        @keyframes rotateCube {
            from { transform: rotateX(0deg) rotateY(0deg); }
            to { transform: rotateX(360deg) rotateY(360deg); }
        }
        
        .cube-face {
            position: absolute;
            width: 200px;
            height: 200px;
            border: 2px solid rgba(0, 198, 255, 0.3);
            background: rgba(0, 198, 255, 0.05);
            box-shadow: inset 0 0 60px rgba(0, 198, 255, 0.2);
        }
        
        .cube-face:nth-child(1) { transform: rotateY(0deg) translateZ(100px); }
        .cube-face:nth-child(2) { transform: rotateY(90deg) translateZ(100px); }
        .cube-face:nth-child(3) { transform: rotateY(180deg) translateZ(100px); }
        .cube-face:nth-child(4) { transform: rotateY(-90deg) translateZ(100px); }
        .cube-face:nth-child(5) { transform: rotateX(90deg) translateZ(100px); }
        .cube-face:nth-child(6) { transform: rotateX(-90deg) translateZ(100px); }
        
        /* Particles */
        .particle {
            position: absolute;
            width: 4px;
            height: 4px;
            background: #00C6FF;
            border-radius: 50%;
            box-shadow: 0 0 10px #00C6FF;
            animation: particleFloat 3s infinite ease-in-out;
        }
        
        @keyframes particleFloat {
            0%, 100% { transform: translateY(0) translateX(0); opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { transform: translateY(-100vh) translateX(50px); opacity: 0; }
        }
        
        .particle:nth-child(1) { left: 10%; animation-delay: 0s; }
        .particle:nth-child(2) { left: 20%; animation-delay: 0.5s; }
        .particle:nth-child(3) { left: 30%; animation-delay: 1s; }
        .particle:nth-child(4) { left: 40%; animation-delay: 1.5s; }
        .particle:nth-child(5) { left: 50%; animation-delay: 2s; }
        .particle:nth-child(6) { left: 60%; animation-delay: 2.5s; }
        .particle:nth-child(7) { left: 70%; animation-delay: 0.8s; }
        .particle:nth-child(8) { left: 80%; animation-delay: 1.2s; }
        .particle:nth-child(9) { left: 90%; animation-delay: 1.8s; }
        
        /* Title */
        .splash-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 7rem;
            font-weight: 900;
            background: linear-gradient(45deg, #00C6FF, #FF00E5, #00C6FF);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: gradientShift 3s ease infinite, glowPulse 2s ease-in-out infinite;
            text-shadow: 0 0 80px rgba(0, 198, 255, 0.8),
                         0 0 120px rgba(255, 0, 229, 0.6);
            letter-spacing: 10px;
            position: relative;
            z-index: 10;
        }
        
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        @keyframes glowPulse {
            0%, 100% { filter: brightness(1) drop-shadow(0 0 20px #00C6FF); }
            50% { filter: brightness(1.3) drop-shadow(0 0 40px #FF00E5); }
        }
        
        /* Subtitle with Typing Effect */
        .splash-subtitle {
            font-family: 'Rajdhani', sans-serif;
            font-size: 2rem;
            color: #fff;
            margin-top: 20px;
            letter-spacing: 8px;
            position: relative;
            z-index: 10;
            overflow: hidden;
            border-right: 3px solid #00C6FF;
            white-space: nowrap;
            animation: typing 2s steps(30) 0.5s forwards, blink 0.75s step-end infinite;
            width: 0;
        }
        
        @keyframes typing {
            from { width: 0; }
            to { width: 100%; }
        }
        
        @keyframes blink {
            50% { border-color: transparent; }
        }
        
        /* Loader Bar */
        .loader-bar {
            width: 400px;
            height: 6px;
            background: rgba(255,255,255,0.1);
            margin-top: 60px;
            border-radius: 10px;
            overflow: hidden;
            position: relative;
            z-index: 10;
            box-shadow: 0 0 20px rgba(0, 198, 255, 0.3);
        }
        
        .loader-fill {
            height: 100%;
            background: linear-gradient(90deg, #00C6FF, #FF00E5, #00C6FF);
            background-size: 200% 100%;
            width: 0%;
            animation: load 3.5s cubic-bezier(0.65, 0, 0.35, 1) forwards,
                       shimmer 1.5s infinite;
            box-shadow: 0 0 30px #00C6FF, 0 0 60px #FF00E5;
            position: relative;
        }
        
        .loader-fill::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            animation: pulse 1s infinite;
        }
        
        @keyframes load {
            0% { width: 0%; }
            20% { width: 30%; }
            40% { width: 50%; }
            60% { width: 75%; }
            80% { width: 90%; }
            100% { width: 100%; }
        }
        
        @keyframes shimmer {
            0% { background-position: 0% 0%; }
            100% { background-position: 200% 0%; }
        }
        
        @keyframes pulse {
            0%, 100% { transform: translateX(-100%); }
            50% { transform: translateX(100%); }
        }
        
        /* Hide Streamlit Elements */
        [data-testid="stSidebar"], 
        [data-testid="stToolbar"], 
        .main {
            display: none !important;
        }
    </style>
    
    <div class="splash-container">
        <!-- Particles -->
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        
        <!-- 3D Cube -->
        <div class="cube-container">
            <div class="cube">
                <div class="cube-face"></div>
                <div class="cube-face"></div>
                <div class="cube-face"></div>
                <div class="cube-face"></div>
                <div class="cube-face"></div>
                <div class="cube-face"></div>
            </div>
        </div>
        
        <!-- Title & Subtitle -->
        <div class="splash-title">EPDK</div>
        <div class="splash-subtitle">STRATEJİK PAZAR ANALİZİ</div>
        
        <!-- Loader -->
        <div class="loader-bar">
            <div class="loader-fill"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    time.sleep(3.5)
    st.session_state['splash_shown'] = True
    st.rerun()
