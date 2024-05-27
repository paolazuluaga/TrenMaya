from qgis.core import (
    QgsFeature, QgsField, QgsGeometry, QgsPointXY, QgsVectorLayer,
    QgsWkbTypes, QgsProject, QgsProcessing, QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource, QgsProcessingParameterField,
    QgsProcessingParameterFeatureSink, QgsFeatureSink  # Importar QgsFeatureSink aquí
)
from PyQt5.QtCore import QVariant


class CalculateMeasurements(QgsProcessingAlgorithm):
    INPUT_POINTS = 'INPUT_POINTS'
    INPUT_LINES = 'INPUT_LINES'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_POINTS,
                'Input Point Layer',
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LINES,
                'Input Line Layer',
                [QgsProcessing.TypeVectorLine]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                'Output Layer'
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        points_layer = self.parameterAsVectorLayer(parameters, self.INPUT_POINTS, context)
        lines_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LINES, context)
        
        # Verificación de que ambos CRS estén en metros y no sean geográficos
        if points_layer.crs().isGeographic() or lines_layer.crs().isGeographic():
            feedback.reportError("Ambas capas deben estar en un sistema de coordenadas proyectado en metros.", True)
            return {}

        # Verificación de que ambas capas tengan el mismo CRS
        if points_layer.crs().postgisSrid() != lines_layer.crs().postgisSrid():
            feedback.reportError("Las capas deben tener el mismo sistema de proyección.", True)
            return {}

        # Create the output layer
        output_fields = points_layer.fields()
        output_fields.append(QgsField('Measure', QVariant.Double))

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               output_fields, QgsWkbTypes.Point, points_layer.sourceCrs())

        # Process each point
        for point_feat in points_layer.getFeatures():
            point_geom = point_feat.geometry()
            point = point_geom.asPoint()

            # Find the closest line and calculate the measure
            closest_line = self.findClosestLine(point, lines_layer)
            if closest_line:
                measure = self.calculateMeasureOnLine(point, closest_line)

                # Create a new feature with additional fields
                new_feat = QgsFeature(output_fields)
                new_feat.setGeometry(point_geom)
                for field in points_layer.fields().names():
                    new_feat[field] = point_feat[field]
                new_feat['Measure'] = measure
                sink.addFeature(new_feat, QgsFeatureSink.FastInsert)

        return {self.OUTPUT: dest_id}

    def findClosestLine(self, point, lines_layer):
        min_distance = float('inf')
        closest_feature = None

        for feature in lines_layer.getFeatures():
            line_geom = feature.geometry()
            # closestSegmentWithContext() devuelve una tupla con información, donde el segundo elemento es la distancia
            result = line_geom.closestSegmentWithContext(QgsPointXY(point))
            distance = result[2]  # La distancia es el tercer elemento de la tupla devuelta

            if distance < min_distance:
                min_distance = distance
                closest_feature = feature

        return closest_feature

    def calculateMeasureOnLine(self, point, line_feature):
        """
        Calculates the measure along a line from its start to the closest point on the line given a point.
        
        Args:
        point (QgsPointXY): The reference point for measuring.
        line_feature (QgsFeature): The line feature on which the measurement is calculated.
        
        Returns:
        float: The measured distance along the line from its start to the closest point.
        """
        line_geom = line_feature.geometry()  # Asegura la definición de line_geom
        # Closest point calculation returns a tuple, where the second element is the actual closest point
        closest_point_info = line_geom.closestSegmentWithContext(QgsPointXY(point))
        closest_point = QgsPointXY(closest_point_info[1])  # Ensure it's a QgsPointXY object
        measure = line_geom.lineLocatePoint(QgsGeometry.fromPointXY(closest_point))


        return measure


    def name(self):
        return 'calculate_measurements'

    def displayName(self):
        return 'Calculate Measurements'

    def group(self):
        return 'LRS Tools'

    def groupId(self):
        return 'lrstools'

    def createInstance(self):
        return CalculateMeasurements()
