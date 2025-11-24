declare module 'react-sparklines' {
  import { Component } from 'react';

  export interface SparklinesProps {
    data: number[];
    width?: number;
    height?: number;
    margin?: number;
    min?: number;
    max?: number;
    limit?: number;
    style?: React.CSSProperties;
    children?: React.ReactNode;
  }

  export interface SparklinesLineProps {
    color?: string;
    style?: React.CSSProperties;
    onMouseMove?: (event: React.MouseEvent) => void;
  }

  export interface SparklinesBarsProps {
    color?: string;
    style?: React.CSSProperties;
    margin?: number;
  }

  export interface SparklinesSpotsProps {
    size?: number;
    style?: React.CSSProperties;
    spotColors?: { [key: string]: string };
  }

  export interface SparklinesReferenceLineProps {
    type?: 'max' | 'min' | 'mean' | 'avg' | 'median' | 'custom';
    value?: number;
    style?: React.CSSProperties;
  }

  export interface SparklinesNormalBandProps {
    style?: React.CSSProperties;
  }

  export interface SparklinesTextProps {
    text?: string;
    point?: { x: number; y: number };
    fontSize?: number;
    fontFamily?: string;
    fontStyle?: string;
    fontWeight?: string;
    fill?: string;
  }

  export class Sparklines extends Component<SparklinesProps> {}
  export class SparklinesLine extends Component<SparklinesLineProps> {}
  export class SparklinesBars extends Component<SparklinesBarsProps> {}
  export class SparklinesSpots extends Component<SparklinesSpotsProps> {}
  export class SparklinesReferenceLine extends Component<SparklinesReferenceLineProps> {}
  export class SparklinesNormalBand extends Component<SparklinesNormalBandProps> {}
  export class SparklinesText extends Component<SparklinesTextProps> {}
}

