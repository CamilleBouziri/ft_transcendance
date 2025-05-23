// --------------------------------------------- //
// ------- 3D PONG built with Three.JS --------- //
// --------------------------------------------- //


var paddle2DirY = 0;

var renderer, scene, camera, pointLight, spotLight;
var fieldWidth = 400, fieldHeight = 200;

// Paddles
var paddleWidth, paddleHeight, paddleDepth, paddleQuality;
var paddleSpeed = 5;

// Ball
var ball, paddle1, paddle2;
var ballSpeed = 2.5;
var ballDirX = 1, ballDirY = 1;

// Scores
var score1 = 0, score2 = 0;
var maxScore = 11;

// Camera
var cameraSide = 0;

// Game mode
var mode = "2players"; 

// For pause
var paused = false;

// ------------------- FUNCTION RECUP SETTING ENRE FRONT -------------------
function getSettings() {
    const savedSettings = localStorage.getItem('pongSettings');
    return savedSettings ? JSON.parse(savedSettings) : null;
}

// ------------------- FUNCTION TO TOGGLE PAUSE -------------------
function togglePause() {
    paused = !paused;
    console.log(paused ? "Game paused" : "Game resumed");
}

// ------------------- CAMERA PHYSICS -------------------
function cameraPhysics() {
    spotLight.position.copy(camera.position);
    spotLight.position.z += 20;

    if (cameraSide === 0) {
        camera.position.x = paddle1.position.x - 100;
        camera.position.z = paddle1.position.z + 100 + 0.04 * (-ball.position.x + paddle1.position.x);

        camera.rotation.x = -0.01 * (ball.position.y) * Math.PI / 180;
        camera.rotation.y = -60 * Math.PI / 180;
        camera.rotation.z = -90 * Math.PI / 180;
    } else {
        camera.position.x = paddle2.position.x + 100;
        camera.position.z = paddle2.position.z + 100 + 0.04 * (ball.position.x - paddle2.position.x);

        camera.rotation.x = -0.01 * (ball.position.y) * Math.PI / 180;
        camera.rotation.y = +60 * Math.PI / 180;
        camera.rotation.z = +90 * Math.PI / 180;
    }
}

// ------------------- SETUP -------------------
function setup() {
    const settings = getSettings();
    if (settings) {
        maxScore = settings.maxScore;
        mode = settings.mode;
    }

    // Initialiser les scores à 0 et mettre à jour l'affichage
    score1 = 0;
    score2 = 0;
    document.querySelector('#score1').textContent = '0';
    document.querySelector('#score2').textContent = '0';
    document.getElementById("winnerBoard").innerHTML = "First to " + maxScore + " wins!";
    
    createScene(settings);
    draw();
}

// ------------------- CREATE SCENE -------------------
function createScene(settings) {
    var WIDTH = 640, HEIGHT = 360;
    var VIEW_ANGLE = 50,
        ASPECT = WIDTH / HEIGHT,
        NEAR = 0.1,
        FAR = 10000;

    var c = document.getElementById("gameCanvas");
    renderer = new THREE.WebGLRenderer();
    camera = new THREE.PerspectiveCamera(VIEW_ANGLE, ASPECT, NEAR, FAR);
    scene = new THREE.Scene();

    scene.add(camera);
    camera.position.z = 320;
    renderer.setSize(WIDTH, HEIGHT);
    c.appendChild(renderer.domElement);

    // Terrain
    var terrainColor = settings ? settings.terrainColor : 0x0e18a9;
    var planeMaterial = new THREE.MeshLambertMaterial({ color: terrainColor });
    var plane = new THREE.Mesh(
        new THREE.PlaneGeometry(fieldWidth * 0.95, fieldHeight, 10, 10),
        planeMaterial
    );
    plane.name = 'terrain';
    scene.add(plane);
    plane.receiveShadow = true;

    // Line
    var lineMaterial = new THREE.MeshLambertMaterial({ color: 0xffffff });
    var centerLine = new THREE.Mesh(
        new THREE.PlaneGeometry(fieldWidth * 0.95, 2),
        lineMaterial
    );
    centerLine.position.set(0, 0, 1);
    scene.add(centerLine);

    // Table
    var tableMaterial = new THREE.MeshLambertMaterial({ color: 0x111111 });
    var table = new THREE.Mesh(
        new THREE.CubeGeometry(
            fieldWidth * 1.05,
            fieldHeight * 1.03,
            100
        ),
        tableMaterial
    );
    table.position.z = -51;
    table.receiveShadow = true;
    scene.add(table);

    // Background below the table
    var backgroundMaterial = new THREE.MeshLambertMaterial({ color: 0x555555 });
    var background = new THREE.Mesh(
        new THREE.CubeGeometry(1000, 1000, 10),
        backgroundMaterial
    );
    background.position.z = -150;
    scene.add(background);

    // Ball
    var ballColor = settings ? settings.ballColor : 0xffffff;
    var sphereMaterial = new THREE.MeshLambertMaterial({ color: ballColor });
    ball = new THREE.Mesh(new THREE.SphereGeometry(5, 6, 6), sphereMaterial);
    ball.position.set(0, 0, 5);
    ball.receiveShadow = true;
    ball.castShadow = true;
    scene.add(ball);

    // Paddles
    paddleWidth = 10;
    paddleHeight = 30;
    paddleDepth = 10;

    var paddleColor1 = settings ? settings.paddleColor1 : 0xffffff;
    var paddleColor2 = settings ? settings.paddleColor2 : 0xffffff;

    var paddle1Material = new THREE.MeshLambertMaterial({ color: paddleColor1 });
    paddle1 = new THREE.Mesh(
        new THREE.CubeGeometry(paddleWidth, paddleHeight, paddleDepth),
        paddle1Material
    );
    paddle1.receiveShadow = false;
    paddle1.castShadow = false;
    scene.add(paddle1);

    var paddle2Material = new THREE.MeshLambertMaterial({ color: paddleColor2 });
    paddle2 = new THREE.Mesh(
        new THREE.CubeGeometry(paddleWidth, paddleHeight, paddleDepth),
        paddle2Material
    );
    paddle2.receiveShadow = false;
    paddle2.castShadow = false;
    scene.add(paddle2);

    paddle1.position.x = -fieldWidth / 2 + paddleWidth;
    paddle2.position.x = fieldWidth / 2 - paddleWidth;
    paddle1.position.z = paddleDepth;
    paddle2.position.z = paddleDepth;

    // Lights
    pointLight = new THREE.PointLight(0xF8D898);
    pointLight.position.set(-1000, 0, 1000);
    pointLight.intensity = 3;
    pointLight.distance = 10000;
    scene.add(pointLight);

    spotLight = new THREE.SpotLight(0xF8D898);
    spotLight.position.set(0, 0, 460);
    spotLight.target = new THREE.Object3D();
    spotLight.target.position.set(0, 0, 0);
    scene.add(spotLight.target);

    spotLight.intensity = 3;
    spotLight.castShadow = true;
    scene.add(spotLight);

    renderer.shadowMapEnabled = true;
}

// ------------------- DRAW -------------------
function draw() {
    renderer.render(scene, camera);
    requestAnimationFrame(draw);

    if (!paused) {
        ballPhysics();
        paddlePhysics();
        cameraPhysics();
        playerPaddleMovement();
        if (mode === "ia") {
            opponentPaddleMovement();
        } else {
            player2PaddleMovement();
        }
    }
}

// ------------------- BALL PHYSICS -------------------
function ballPhysics() {
    if (ball.position.x <= -fieldWidth / 2) {
        score2++;
        document.querySelector('#score2').textContent = score2;
        resetBall(2);
        matchScoreCheck();
    }
    if (ball.position.x >= fieldWidth / 2) {
        score1++;
        document.querySelector('#score1').textContent = score1;
        resetBall(1);
        matchScoreCheck();
    }
    if (ball.position.y <= -fieldHeight / 2 || ball.position.y >= fieldHeight / 2) {
        ballDirY = -ballDirY;
    }
    ball.position.x += ballDirX * ballSpeed;
    ball.position.y += ballDirY * ballSpeed;

    if (ballDirY > ballSpeed * 2) {
        ballDirY = ballSpeed * 2;
    } else if (ballDirY < -ballSpeed * 2) {
        ballDirY = -ballSpeed * 2;
    }
}

// ------------------- PLAYER PADDLE MOVEMENT -------------------
function playerPaddleMovement() {
    paddle1DirY = 0;
    if (Key.isDown(Key.A)) {
        paddle1DirY = paddleSpeed * 0.5;
    } else if (Key.isDown(Key.D)) {
        paddle1DirY = -paddleSpeed * 0.5;
    }
    paddle1.position.y += paddle1DirY;
    paddle1.position.y = Math.max(Math.min(paddle1.position.y, fieldHeight * 0.45), -fieldHeight * 0.45);
}

// ------------------- PLAYER 2 PADDLE MOVEMENT -------------------
function player2PaddleMovement() {
    paddle2DirY = 0;
    if (Key.isDown(Key.LEFT)) {
        paddle2DirY = paddleSpeed * 0.5;
    } else if (Key.isDown(Key.RIGHT)) {
        paddle2DirY = -paddleSpeed * 0.5;
    }
    paddle2.position.y += paddle2DirY;
    paddle2.position.y = Math.max(Math.min(paddle2.position.y, fieldHeight * 0.45), -fieldHeight * 0.45);
}

// ------------------- OPPONENT PADDLE MOVEMENT -------------------
function opponentPaddleMovement() {
    paddle2DirY = (ball.position.y - paddle2.position.y) * 0.2;
    paddle2.position.y += Math.sign(paddle2DirY) * Math.min(Math.abs(paddle2DirY), paddleSpeed);
    paddle2.position.y = Math.max(Math.min(paddle2.position.y, fieldHeight * 0.45), -fieldHeight * 0.45);
}

// ------------------- PADDLE PHYSICS -------------------
function paddlePhysics() {
    if (
        ball.position.x <= paddle1.position.x + paddleWidth &&
        ball.position.x >= paddle1.position.x &&
        ball.position.y <= paddle1.position.y + paddleHeight / 2 &&
        ball.position.y >= paddle1.position.y - paddleHeight / 2 &&
        ballDirX < 0
    ) {
        ballDirX = -ballDirX;
        ballDirY -= paddle1DirY * 0.3;
    }

    if (
        ball.position.x <= paddle2.position.x + paddleWidth &&
        ball.position.x >= paddle2.position.x &&
        ball.position.y <= paddle2.position.y + paddleHeight / 2 &&
        ball.position.y >= paddle2.position.y - paddleHeight / 2 &&
        ballDirX > 0
    ) {
        ballDirX = -ballDirX;
        ballDirY -= paddle2DirY * 0.3;
    }
}

// ------------------- RESET BALL -------------------
function resetBall(loser) {
    // Reset ball position
    ball.position.set(0, 0, 5);
    ballDirX = loser === 1 ? 1 : -1;
    ballDirY = 1;

    // Reset paddles positions
    paddle1.position.y = 0;
    paddle2.position.y = 0;
    
    // Reset paddle directions
    paddle1DirY = 0;
    paddle2DirY = 0;
}

// ------------------- MATCH SCORE CHECK -------------------
function matchScoreCheck() {
    if (score1 >= maxScore || score2 >= maxScore) {
        ballSpeed = 0;
        
        const player1Name = document.querySelector('#player1 h2').textContent;
        const player2Name = document.querySelector('#player2 h2').textContent;
        const winner = score1 > score2 ? player1Name : player2Name;
        
        // Sauvegarder et afficher le résultat
        displayWinner(winner, score1 > score2 ? player2Name : player1Name, 
                     Math.max(score1, score2), Math.min(score1, score2));
    }
}

function displayWinner(winner, loser, winnerScore, loserScore) {
    const overlay = document.getElementById('gameResultOverlay');
    const winnerText = overlay.querySelector('.winner-text');
    const scoreText = overlay.querySelector('.score-text');
    
    winnerText.textContent = `Vainqueur : ${winner}`;
    scoreText.textContent = `Score Final : ${winnerScore} - ${loserScore}`;
    
    // Sauvegarder les données pour handleGameEnd
    localStorage.setItem('gameResult', JSON.stringify({
        winner: winner,
        player1Score: score1,
        player2Score: score2,
        player1Name: document.querySelector('#player1 h2').textContent,
        player2Name: document.querySelector('#player2 h2').textContent
    }));
    
    overlay.style.display = 'flex';
}

function handleGameEnd() {
    const gameData = JSON.parse(localStorage.getItem('gameResult'));
    if (!gameData) return;

    const formData = new URLSearchParams();
    formData.append('winner', gameData.winner);
    formData.append('player1_score', gameData.player1Score);
    formData.append('player2_score', gameData.player2Score);

    fetch('/save-result/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            localStorage.removeItem('gameResult');
            window.location.href = '/dashboard/';
        }
    })
    .catch(error => console.error('Erreur:', error));
}

// Fonction utilitaire pour obtenir le token CSRF
function getCSRFToken() {
    return document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1] || '';
}
