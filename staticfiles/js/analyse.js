document.addEventListener("DOMContentLoaded", function() {
    const matplotlibLabel = document.getElementById('matplotlib-label');
    const matplotlibToolsContainer = document.getElementById('matplotlib-tools-container');
    const matplotlibArrow = document.getElementById('matplotlib-arrow');

    const seabornLabel = document.getElementById('seaborn-label');
    const seabornToolsContainer = document.getElementById('seaborn-tools-container');
    const seabornArrow = document.getElementById('seaborn-arrow');

    matplotlibLabel.addEventListener('click', function() {
      matplotlibToolsContainer.classList.toggle('hidden');
      matplotlibArrow.classList.toggle('rotate-180');
    });

    seabornLabel.addEventListener('click', function() {
      seabornToolsContainer.classList.toggle('hidden');
      seabornArrow.classList.toggle('rotate-180');
    });


  });
  