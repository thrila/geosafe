import { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import type { ModalProps } from "../types/modal";
import { X } from "react-feather";

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(", ");

export function Modal({ isOpen, title, onClose, children }: ModalProps) {
  const panelRef = useRef<HTMLElement>(null);
  const previousOverflowRef = useRef<string>("");
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const onCloseRef = useRef(onClose);
  const titleId = useId();

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!isOpen) return;

    previousOverflowRef.current = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    previousFocusRef.current =
      document.activeElement instanceof HTMLElement ? document.activeElement : null;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onCloseRef.current();
        return;
      }

      if (e.key !== "Tab") return;

      const panel = panelRef.current;
      if (!panel) return;

      const focusables = Array.from(
        panel.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
      );
      if (focusables.length === 0) {
        e.preventDefault();
        panel.focus();
        return;
      }

      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement;
      const activeInPanel = active instanceof Node && panel.contains(active);

      if (e.shiftKey) {
        if (!activeInPanel || active === panel || active === first) {
          e.preventDefault();
          last.focus();
        }
      } else if (!activeInPanel || active === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflowRef.current;
      document.removeEventListener("keydown", handleKeyDown);
      previousFocusRef.current?.focus();
    };
  }, [isOpen]);

  // --- Auto-focus panel when modal opens ---
  useEffect(() => {
    if (!isOpen) return;

    // Tiny delay to ensure DOM is painted
    const timeoutId = setTimeout(() => {
      panelRef.current?.focus();
    }, 50);

    return () => clearTimeout(timeoutId);
  }, [isOpen]);

  // --- Don't render if closed ---
  if (!isOpen) return null;

  // --- Portal target (fallback to body) ---
  const portalTarget = document.getElementById("root-modal") ?? document.body;

  // --- Overlay click handler ---
  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // --- Render portal ---
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
        aria-labelledby={titleId}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">

          <h2 className="modal-title" id={titleId}>{title}</h2>
          {/* Close button */}
          <button
            type="button"
            className="panel-close"
            onClick={onClose}
            aria-label="Close modal"
          >
            <X size={24} aria-hidden="true" />
          </button>
        </div>

        <span className="panel-divider" aria-hidden="true" />

        {children}
      </section>
    </div>,
    portalTarget
  );
}
