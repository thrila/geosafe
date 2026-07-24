import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import type { ModalProps } from "../types/modal";
import { X } from "react-feather";


export function Modal({ isOpen, title, onClose, children }: ModalProps) {
  const panelRef = useRef<HTMLElement>(null);
  const previousOverflowRef = useRef<string>("");
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!isOpen) return;

    previousOverflowRef.current = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onCloseRef.current();
      }
    };
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflowRef.current;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  // --- 2. Auto-focus panel when modal opens ---
  useEffect(() => {
    if (!isOpen) return;

    // Tiny delay to ensure DOM is painted
    const timeoutId = setTimeout(() => {
      panelRef.current?.focus();
    }, 50);

    return () => clearTimeout(timeoutId);
  }, [isOpen]);

  // --- 3. Don't render if closed ---
  if (!isOpen) return null;

  // --- 4. Portal target (fallback to body) ---
  const portalTarget = document.getElementById("root-modal") ?? document.body;

  // --- 5. Overlay click handler ---
  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // --- 6. Render portal ---
  return createPortal(
    <div
      className="modal-overlay"
      role="presentation"
      onClick={handleOverlayClick}
    >
      <section
        ref={panelRef}
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">

          <h2 className="modal-title">{title}</h2>
          {/* Close button */}
          <button
            type="button"
            className="panel-close"
            onClick={onClose}
            aria-label="Close modal"
          >
            <X size={24} />
          </button>
        </div>

        <span className="panel-divider" aria-hidden="true" />

        {children}
      </section>
    </div>,
    portalTarget
  );
}
