//////////////////////////
// Gestion du popup de jeu
//////////////////////////

document.addEventListener('DOMContentLoaded', function() {

	// Affiche le popup quand on clique sur le bouton Game

	document.getElementById("game-btn").addEventListener("click", function() {
        document.getElementById("game-popup").style.display = "block";
    });
    
    // Ferme le popup quand on clique sur la croix

	document.getElementById("close-popup").addEventListener("click", function() {
        document.getElementById("game-popup").style.display = "none";
    });
});

