window.addEventListener('keyup', function(event) {
    Key.onKeyup(event);
  }, false);
  
  window.addEventListener('keydown', function(event) {
    Key.onKeydown(event);
  }, false);
  
  var Key = {
    _pressed: {},
  
    A: 65,
    W: 87,
    D: 68,
    S: 83,
    SPACE: 32,
  
    // Ajout des flèches gauche et droite
    LEFT: 37,
    RIGHT: 39,
    
    isDown: function(keyCode) {
      return this._pressed[keyCode];
    },
    
    onKeydown: function(event) {
      this._pressed[event.keyCode] = true;
    },
    
    onKeyup: function(event) {
      delete this._pressed[event.keyCode];
    }
  };
  