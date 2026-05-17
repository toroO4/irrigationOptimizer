"""
Service — Export Operations.

Handles CSV and GeoJSON export generation.
"""

import csv
import io
import json
from typing import Any, Dict, List

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class ExportService:
    """Generates CSV and GeoJSON exports from schedule/prediction data."""

    def export_schedules_csv(self, schedules: List[Dict[str, Any]]) -> str:
        """
        Export irrigation schedules as a CSV string.

        Args:
            schedules: List of schedule dictionaries.

        Returns:
            CSV formatted string.
        """
        if not schedules:
            return ""

        output = io.StringIO()
        fieldnames = list(schedules[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in schedules:
            # Flatten nested dicts for CSV
            flat = {}
            for k, v in row.items():
                if isinstance(v, dict):
                    flat[k] = json.dumps(v)
                else:
                    flat[k] = v
            writer.writerow(flat)

        logger.info("Exported %d schedules to CSV", len(schedules))
        return output.getvalue()

    def export_geojson(
        self,
        fields: List[Dict[str, Any]],
        predictions: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a GeoJSON FeatureCollection from field data.

        Args:
            fields: List of field dictionaries with lat/lon coordinates.
            predictions: Optional moisture predictions to attach as properties.

        Returns:
            GeoJSON FeatureCollection dictionary.
        """
        features = []

        for i, field in enumerate(fields):
            lat = field.get("centroid_lat", field.get("latitude", 18.5))
            lon = field.get("centroid_lon", field.get("longitude", 73.8))

            properties = {
                "name": field.get("name", f"Field-{i + 1}"),
                "crop_type": field.get("crop_type", "unknown"),
                "soil_type": field.get("soil_type", "unknown"),
                "area_hectares": field.get("area_hectares", 1.0),
            }

            if predictions and i < len(predictions):
                properties.update({
                    "predicted_moisture": predictions[i].get("predicted_moisture"),
                    "confidence": predictions[i].get("confidence"),
                })

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat],
                },
                "properties": properties,
            }
            features.append(feature)

        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "total_fields": len(features),
                "crs": "EPSG:4326",
            },
        }

        logger.info("Generated GeoJSON with %d features", len(features))
        return geojson


# Singleton
export_service = ExportService()
