document.getElementById('openPopupButton').addEventListener('click', function () {
    document.getElementById('popupSection').classList.remove('hidden');  
});

document.getElementById('closePopupButton').addEventListener('click', function () {
    document.getElementById('popupSection').classList.add('hidden');  
});

