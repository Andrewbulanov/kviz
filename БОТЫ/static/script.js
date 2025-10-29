// Бесконечный конфетти-эффект на победном экране
let confettiLoop = null;

window.showWinnerOverlay = function(name, score){
  const overlay = document.getElementById('winnerOverlay');
  if(!overlay) return;

  document.getElementById('winnerText').innerText = "🏆 Победитель: " + (name || "");
  document.getElementById('winnerScore').innerText = "Очки: " + (score || 0);

  overlay.classList.remove('hidden');

  // запускаем конфетти только если ещё не запущено
  if(!confettiLoop){
    launchConfetti();
    confettiLoop = setInterval(launchConfetti, 1200); // повтор каждые ~1.2 сек
  }
};


// Конфетти (полоски), но теперь в повторном цикле
function launchConfetti(){
  const box = document.getElementById('confetti');
  if(!box) return;
  
  const colors = ["#00f5d4", "#00e6ff", "#f15bb5", "#5e60ce", "#ffffff", "#ffd700"];

  // создаём ~30 штук за волну, но они будут появляться постоянно
  for (let i = 0; i < 30; i++){
    const piece = document.createElement("div");
    piece.className = "confetti";

    const sizeW = 6 + Math.random()*6;
    const sizeH = 12 + Math.random()*8;
    piece.style.width = sizeW + "px";
    piece.style.height = sizeH + "px";

    piece.style.left = (Math.random() * 100) + "%";
    piece.style.top = (-Math.random() * 40) + "px";

    piece.style.background = colors[Math.floor(Math.random()*colors.length)];

    const fallTime = 900 + Math.random()*900; // 0.9 - 1.8 sec fall
    const delay = Math.random()*200;
    piece.style.animation = `fall ${fallTime}ms ease-out forwards, spin ${fallTime}ms linear forwards`;
    piece.style.animationDelay = delay + "ms";

    box.appendChild(piece);

    // удалить элемент после завершения, чтоб DOM не переполнялся
    setTimeout(() => {
      if (piece && piece.parentNode) {
        piece.parentNode.removeChild(piece);
      }
    }, fallTime + 400);
  }
}
