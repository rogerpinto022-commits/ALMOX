st.markdown("""
<style>
/* MARCA D'ÁGUA EM DESTAQUE - REPETIDA */
.watermark-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 0;
    pointer-events: none;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-content: center;
    gap: 120px;
    opacity: 0.18;
}
.watermark-item {
    font-size: 38px;
    font-weight: 900;
    color: #ff4e00;
    transform: rotate(-35deg);
    text-shadow: 2px 2px 0 #000, 0 0 10px rgba(255,78,0,0.8);
    border: 4px solid #ff4e00;
    padding: 12px 22px;
    border-radius: 12px;
    background: rgba(0,0,0,0.05);
    white-space: nowrap;
    font-family: 'Montserrat', sans-serif;
}
.watermark-top {
    position: fixed;
    top: 10px;
    right: 20px;
    font-size: 15px;
    font-weight: 900;
    color: #fff;
    z-index: 9999;
    pointer-events: none;
    background: linear-gradient(90deg, #ff4e00, #ff0000);
    padding: 8px 18px;
    border-radius: 25px;
    border: 2px solid #000;
    box-shadow: 0 0 15px #ff4e00, 0 4px 0 #000;
    text-shadow: 1px 1px 0 #000;
}
.watermark-bottom {
    position: fixed;
    bottom: 10px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 14px;
    font-weight: 900;
    color: #ff4e00;
    z-index: 9999;
    pointer-events: none;
    background: #000;
    padding: 6px 20px;
    border-radius: 20px;
    border: 2px solid #ff4e00;
    box-shadow: 0 0 12px #ff4e00;
}
.block-container { position:relative; z-index:1; }
</style>

<div class="watermark-container">
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS</div>
    <div class="watermark-item">REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS</div>
</div>

<div class="watermark-top">🔥 REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS 🔥</div>
<div class="watermark-bottom">⚠️ SISTEMA PROTEGIDO - REFORMA DE FORNOS - MATERIAIS REFRATÁRIOS ⚠️</div>
""", unsafe_allow_html=True)
