import Swal from 'sweetalert2';
// Función para mostrar mensaje emergente con SweetAlert2
function showMessage() {
    Swal.fire({
        title: 'Tutorados seleccionados',
        icon: 'success',
        confirmButtonText: 'OK'
    });
}

// Asegúrate de que el documento esté listo antes de ejecutar cualquier código JavaScript
document.addEventListener('DOMContentLoaded', function () {
    // Función para mostrar mensaje emergente con SweetAlert2
    showMessage();

    // Capturamos el evento click del botón y llamamos a la función showMessage
    document.getElementById('assign-tutorados').addEventListener('click', showMessage);
});

// alerts.js

