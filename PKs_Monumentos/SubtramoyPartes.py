from qgis.core import (QgsProcessing, QgsFeatureSink, QgsProcessingAlgorithm, QgsApplication,
                       QgsProcessingParameterFeatureSource, QgsProcessingParameterFeatureSink,
                       QgsField, QgsFields, QgsFeature)
from qgis.PyQt.QtCore import QVariant
import processing

class SubtramoYParte(QgsProcessingAlgorithm):
    INPUT_LAYER = 'INPUT_LAYER'
    OUTPUT_LAYER = 'OUTPUT_LAYER'

    def tr(self, string):
        return QgsApplication.translate("SubtramoYParte", string)

    def createInstance(self):
        return SubtramoYParte()

    def name(self):
        return 'subtramo_y_parte'

    def displayName(self):
        return self.tr('Calcula Subtramo y Parte')

    def group(self):
        return self.tr('LRS Tools')

    def groupId(self):
        return 'lrstools'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LAYER,
                self.tr('Capa de puntos con LRS calculado'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LAYER,
                self.tr('Capa de salida')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.INPUT_LAYER, context)
        
        output_fields = source.fields()
        #output_fields.append(QgsField('Subtramo', QVariant.Int))
        #output_fields.append(QgsField('Part', QVariant.Int))
        output_fields.append(QgsField('Monumentos_Subtramo_', QVariant.String))  # New field

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT_LAYER, context,
                                               output_fields, source.wkbType(), source.sourceCrs())

        features = source.getFeatures()
        sorted_features = sorted(features, key=lambda x: x['Measure'])

        subtramo = 0
        part = 1
        count = 0
        last_subtramo = None

        for current, feature in enumerate(sorted_features):
            new_feature = QgsFeature(output_fields)
            new_feature.setGeometry(feature.geometry())
            for field in feature.fields().names():
                new_feature[field] = feature[field]

            if last_subtramo is None or feature['Measure'] < 27000:
                subtramo = 1
            elif feature['Measure'] >= 47000:
                subtramo = 3
            else:
                subtramo = 2

            if last_subtramo is not None and subtramo != last_subtramo:
                part = 1
                count = 0

            if count >= 1000:
                part += 1
                count = 0

            subtramo_part_text = f"{subtramo}_Part_{part}"  # Formatting here
            #new_feature['Subtramo'] = subtramo
            #new_feature['Part'] = part
            new_feature['Monumentos_Subtramo_'] = subtramo_part_text  # Set the formatted text
            sink.addFeature(new_feature, QgsFeatureSink.FastInsert)

            last_subtramo = subtramo
            count += 1

        return {self.OUTPUT_LAYER: dest_id}
