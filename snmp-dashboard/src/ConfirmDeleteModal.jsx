import React from 'react';
import './ConfirmDeleteModal.css'; // We will create this CSS file next

/**
 * A custom modal for delete confirmation.
 * * @param {boolean} isOpen - Whether the modal is visible
 * @param {function} onClose - Called when 'Cancel' is clicked
 * @param {function} onSoftDelete - Called when 'Delete from Dashboard' is clicked
 * @param {function} onHardDelete - Called when 'Delete from Database' is clicked
 * @param {boolean} showHardDelete - If true, shows the 'Delete from Database' button
 */
function ConfirmDeleteModal({ 
  isOpen, 
  onClose, 
  onSoftDelete, 
  onHardDelete,
  showHardDelete 
}) {
  if (!isOpen) {
    return null;
  }

  return (
    // The modal overlay
    <div className="modal-overlay">
      
      {/* The modal content box */}
      <div className="modal-content">
        <h3>Delete Device</h3>
        <p>How would you like to proceed?</p>
        
        <div className="modal-actions">
          {/* This is the "Soft Delete" button.
            It's always visible for all users.
          */}
          <button 
            className="modal-button button-soft-delete" 
            onClick={onSoftDelete}
          >
            Hide from Dashboard
          </button>
          
          {/* This is the "Hard Delete" button.
            It ONLY appears if the 'showHardDelete' prop is true.
          */}
          {showHardDelete && (
            <button 
              className="modal-button button-hard-delete" 
              onClick={onHardDelete}
            >
              Delete from Database
            </button>
          )}

          {/* The "Cancel" button */}
          <button 
            className="modal-button button-cancel" 
            onClick={onClose}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmDeleteModal;