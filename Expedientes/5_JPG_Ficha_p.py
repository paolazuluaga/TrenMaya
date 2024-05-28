"""
Model exported as python.
Name : modelo
Group : 
With QGIS : 33601
Author: Paola Mejia-Zuluaga
Date: 27/04/2024
Modified date: 28/04/2024
"""
from qgis.core import (QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterVectorLayer, QgsProcessingParameterFolderDestination, 
                       QgsProject, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutSize, 
                       QgsLayoutExporter, QgsRasterLayer, QgsSingleBandPseudoColorRenderer, 
                       QgsColorRampShader, QgsRasterShader, QgsApplication, QgsRasterBandStats,
                       QgsRectangle, QgsProcessingParameterNumber, QgsProcessingParameterString)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QCoreApplication
import os

class ExportLayoutAlgorithm(QgsProcessingAlgorithm):
    ORTO_LAYER = 'ORTO_LAYER'
    RVT_LAYER = 'RVT_LAYER'
    DEM_LAYER = 'DEM_LAYER'
    AREA_LAYER = 'AREA_LAYER'  # Capa vectorial que define el área de interés
    BUFFER_FACTOR = 'BUFFER_FACTOR'  # New parameter for buffer factor
    BASE_NAME = 'BASE_NAME'  # New parameter for optional base name
    OUTPUT_FOLDER = 'OUTPUT_FOLDER'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExportLayoutAlgorithm()

    def name(self):
        return 'exportlayout'

    def displayName(self):
        return self.tr('Export Layout for ORTO and RVT')

    def group(self):
        return self.tr('Custom Scripts')

    def groupId(self):
        return 'customscripts'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DEM_LAYER,
                self.tr("Seleccionar DEM")
            )
        )
        
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.ORTO_LAYER,
                self.tr("Seleccionar ORTOFOTO")
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.RVT_LAYER,
                self.tr("Seleccionar RVT")
            )
        )
        self.addParameter(
        QgsProcessingParameterVectorLayer(
            self.AREA_LAYER,
            self.tr("Seleccionar Capa vectorial de referencia")
        )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.BUFFER_FACTOR,
                self.tr("Buffer Factor Zoom Out (optional: 0-2)"),
                QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
                minValue=0.0,
                maxValue=2.0
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.BASE_NAME,
                self.tr("ID Monument"),
                defaultValue=None,  # Default value is None which means it's optional
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_FOLDER,
                self.tr("Ruta carpeta de salida")
            )
        )
        


    def processAlgorithm(self, parameters, context, feedback):
        orto_layer = self.parameterAsRasterLayer(parameters, self.ORTO_LAYER, context)
        rvt_layer = self.parameterAsRasterLayer(parameters, self.RVT_LAYER, context)
        dem_layer = self.parameterAsRasterLayer(parameters, self.DEM_LAYER, context)
        area_layer = self.parameterAsVectorLayer(parameters, self.AREA_LAYER, context)
        buffer_factor = self.parameterAsDouble(parameters, self.BUFFER_FACTOR, context)
        base_name = self.parameterAsString(parameters, self.BASE_NAME, context)
        output_folder = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)

        # Use the provided base name or default to layer name method
        if not base_name:
            # Calculate base name from layer names as fallback
            if rvt_layer:
                base_name = rvt_layer.name()[:8]
            elif orto_layer:
                base_name = orto_layer.name()[:8]
        
        if area_layer:
            extent = area_layer.extent()
            
        # Aplicar simbología pseudocolor al DEM
        if dem_layer:
            self.apply_pseudocolor_style(dem_layer)

        # Apply pseudocolor style to RVT layer
        if rvt_layer:
            layout = self.create_layout(f"{base_name}_LR_RVT", dem_layer, rvt_layer, area_layer,buffer_factor)
            output_path = os.path.join(output_folder, f"{base_name}_LR_RVT.jpg")
            self.export_layout(layout, output_path)

        # Export ORTO layer without applying pseudocolor style
        if orto_layer:
            layout = self.create_layout(f"{base_name}_LR_ORTO", orto_layer, None, area_layer,buffer_factor)
            output_path = os.path.join(output_folder, f"{base_name}_LR_ORTO.jpg")
            self.export_layout(layout, output_path)

        return {self.OUTPUT_FOLDER: output_folder}


    def apply_pseudocolor_style(self, layer):
        if not isinstance(layer, QgsRasterLayer):
            raise Exception("Not a raster layer")
         
        # Obtener estadísticas de la banda 1
        stats = layer.dataProvider().bandStatistics(1, QgsRasterBandStats.All)
        min_val = stats.minimumValue
        max_val = stats.maximumValue

        fcn = QgsColorRampShader()
        fcn.setColorRampType(QgsColorRampShader.Interpolated)
        fcn.setClassificationMode(QgsColorRampShader.EqualInterval)

        # Calcular puntos de la rampa de color proporcionalmente
        range_val = max_val - min_val
        items = [
            QgsColorRampShader.ColorRampItem(min_val + 0.0 * range_val, QColor(78, 123, 67, 179), '0.0000'),
            QgsColorRampShader.ColorRampItem(min_val + 0.57057001536688434 * range_val, QColor(146, 198, 93, 204), '0.5706'),
            QgsColorRampShader.ColorRampItem(min_val + 0.76553135804840566 * range_val, QColor(250, 225, 129, 204), '0.7655'),
            QgsColorRampShader.ColorRampItem(min_val + 0.85990083557433727 * range_val, QColor(190, 145, 72, 204), '0.8599'),
            QgsColorRampShader.ColorRampItem(min_val + 1.0 * range_val, QColor(165, 102, 35, 179), '1.0000')
        ]
        fcn.setColorRampItemList(items)
        
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fcn)
        renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
        layer.setRenderer(renderer)
        layer.triggerRepaint()
        


    def create_layout(self, name, main_layer, background_layer, area_layer,buffer_factor):
        project = QgsProject.instance()
        layout = QgsPrintLayout(project)
        layout.initializeDefaults()
        layout.setName(name)
        
        page_width_mm = 1080 / 96 * 25.4
        page_height_mm = 763 / 96 * 25.4
        layout.pageCollection().pages()[0].setPageSize(QgsLayoutSize(page_width_mm, page_height_mm))
        
        map = QgsLayoutItemMap(layout)
        map.attemptResize(QgsLayoutSize(page_width_mm, page_height_mm))
        
        # Asegurándonos de que la capa está visible y renderizada
        if not main_layer.isValid():
            raise Exception("Layer is not valid")
        if not main_layer.renderer():
            raise Exception("Layer has no renderer")

        
        if area_layer:
            extent = area_layer.extent()
            # Aumentar el extent por un factor para asegurar un margen
            buffer = extent.width() * buffer_factor
            extent_buffered = extent.buffered(buffer)
            
            # Calcular la relación de aspecto de la extensión y el mapa
            extent_aspect = extent_buffered.width() / extent_buffered.height()
            layout_aspect = page_width_mm / page_height_mm
            
            # Ajustar la extensión para que se adapte a la relación de aspecto del layout
            if extent_aspect > layout_aspect:
                new_height = extent_buffered.width() / layout_aspect
                center = extent_buffered.center()
                extent_buffered.setYMinimum(center.y() - new_height / 2)
                extent_buffered.setYMaximum(center.y() + new_height / 2)
            else:
                new_width = extent_buffered.height() * layout_aspect
                center = extent_buffered.center()
                extent_buffered.setXMinimum(center.x() - new_width / 2)
                extent_buffered.setXMaximum(center.x() + new_width / 2)
            
            map.setExtent(extent_buffered)
        else:
            map.setExtent(main_layer.extent())
        
        
        if background_layer:
            map.setLayers([main_layer, background_layer])
        else:
            map.setLayers([main_layer])
        layout.addLayoutItem(map)
        

        return layout

    def export_layout(self, layout, file_path):
        exporter = QgsLayoutExporter(layout)
        settings = QgsLayoutExporter.ImageExportSettings()
        settings.dpi = 96
        exporter.exportToImage(file_path, settings)
