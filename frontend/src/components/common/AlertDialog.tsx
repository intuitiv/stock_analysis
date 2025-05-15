import React from 'react';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';

interface AlertDialogProps {
  open: boolean;
  handleClose: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm?: () => void; // Optional confirm action
}

const AlertDialog: React.FC<AlertDialogProps> = ({
  open,
  handleClose,
  title,
  message,
  confirmText = "OK",
  cancelText = "Cancel",
  onConfirm
}) => {

  const handleConfirmClick = () => {
    if (onConfirm) {
      onConfirm();
    }
    handleClose(); // Close dialog after confirm
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose} // Allow closing by clicking outside
      aria-labelledby="alert-dialog-title"
      aria-describedby="alert-dialog-description"
    >
      <DialogTitle id="alert-dialog-title">
        {title}
      </DialogTitle>
      <DialogContent>
        <DialogContentText id="alert-dialog-description">
          {message}
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        {onConfirm && ( // Only show Cancel if there's a confirm action
          <Button onClick={handleClose} color="secondary"> 
            {cancelText}
          </Button>
        )}
        <Button onClick={handleConfirmClick} autoFocus>
          {confirmText}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AlertDialog;
