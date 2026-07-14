import { FlightMenuItem } from "./data";
import type { ReactNode } from "react";

export type FlightMenuModalProps = {
  activeFlightId: string | null;
  onSelect: (flight: FlightOption) => void;
  onClose: () => void;
  flights?: FlightOption[];
};

export type FlightOption = {
  id: string;
  name: string;
  date: string;
  duration: string;
  location: string;
};

interface ModalProps {
  isOpen: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}
