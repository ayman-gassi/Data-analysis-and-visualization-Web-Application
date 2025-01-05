document.getElementById('openPopupButton').addEventListener('click', function () {
    document.getElementById('popupSection').classList.remove('hidden');  
});

document.getElementById('closePopupButton').addEventListener('click', function () {
    document.getElementById('popupSection').classList.add('hidden');  
});

document.getElementById('openColumnPopup').addEventListener('click', function () {
    document.getElementById('culumnPopUp').classList.remove('hidden');  
});
