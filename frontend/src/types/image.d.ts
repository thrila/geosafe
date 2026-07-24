export type ImageClassificationResponse = {
  filename: string;
  prediction: {
    plant_type: string;
    plant_confidence: number;
    disease: string;
    disease_confidence: number;
  };
  tiles: {
    tile: number;
    prediction: {
      plant_type: string;
      plant_confidence: number;
      disease: string;
      disease_confidence: number;
      all_probabilities: Record<string, number>;
    };
  }[];
  backend: string;
  benchmark_ms: {
    total: number;
  };
};
