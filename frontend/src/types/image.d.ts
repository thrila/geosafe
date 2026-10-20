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
    region: {
      x: number;
      y: number;
      width: number;
      height: number;
      imageWidth: number;
      imageHeight: number;
    };
    prediction: {
      plant_type: string;
      plant_confidence: number;
      disease: string;
      disease_confidence: number;
      all_probabilities: Record<string, number>;
    };
  }[];
  image_url: string | null;
};
