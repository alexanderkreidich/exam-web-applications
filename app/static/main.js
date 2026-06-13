// Заполнение модального окна удаления книги данными выбранной книги.
document.addEventListener('DOMContentLoaded', function () {
    const deleteModal = document.getElementById('deleteModal');
    if (!deleteModal) {
        return;
    }
    deleteModal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        const bookId = button.getAttribute('data-book-id');
        const bookTitle = button.getAttribute('data-book-title');
        deleteModal.querySelector('#deleteBookTitle').textContent = '«' + bookTitle + '»';
        deleteModal.querySelector('#deleteForm').action = '/books/' + bookId + '/delete';
    });
});
