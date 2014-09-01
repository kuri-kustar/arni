import os
import rospy
import rospkg

from python_qt_binding import loadUi
from python_qt_binding.QtGui import QWidget, QPixmap
from python_qt_binding.QtCore import QObject, Qt

from rospy.rostime import Time, Duration
from rospy.timer import Timer

from arni_gui.ros_model import ROSModel
from arni_gui.log_filter_proxy import LogFilterProxy
from arni_gui.log_delegate import LogDelegate

try:
    import pyqtgraph as pg
except ImportError as e:
    print("An error occured trying to import pyqtgraph. Please install pyqtgraph via \"pip install pyqtgraph\".")
    raise


class SelectionWidget(QWidget):
    """
    The SelectionWidget of the ArniGuiDetail-Plugin.
    """
    
    def __init__(self, model):
        """
        Initializes the Widget.
        
        :param model: the model of the widget
        :type model: ROSModel
        """
        super(SelectionWidget, self).__init__()
        self.setObjectName('selection_widget')
        self.__model = model

        # Get path to UI file which is a sibling of this file
        self.rp = rospkg.RosPack()
        ui_file = os.path.join(self.rp.get_path('rqt_arni_gui_detail'), 'resources', 'SelectionWidget.ui')
        # Extend the widget with all attributes and children from UI file
        loadUi(ui_file, self)
        self.setObjectName('SelectionWidgetUi')

        self.__selected_item = None


        self.__draw_graphs = True
        self.__current_combo_box_index = 0

        self.__last_update = rospy.Time.now()

        # TODO self.__graph_layout =
        #TODO self.__graph_dict =

        #TODO fill the dict
        self.__values_dict = {
            "bandwith_mean": 0,
            "bandwith_stddev": 0,
            "bandwith_max": 0,
        }

        self.__logger = self.__model.get_logger()
        self.__log_filter_proxy = LogFilterProxy()       
        self.__log_filter_proxy.filter_by_item(self.__selected_item)
        self.__log_filter_proxy.setDynamicSortFilter(True)        
        self.__log_filter_proxy.setSourceModel(self.__logger.get_representation())
        self.log_tab_tree_view.setModel(self.__log_filter_proxy)
        self.__log_delegate = LogDelegate()
        self.log_tab_tree_view.setItemDelegate(self.__log_delegate)

        self.__style_string = ".detailed_data {\n" \
                               "    font-size: 12\n;" \
                               "}\n"
        self.__style_string = ".erroneous_entry {\n" \
                               "    color: red\n;" \
                               "}\n"

        self.information_tab_text_browser.setStyleSheet(self.__style_string)

        self.range_combo_box.addItem("10 " + self.tr("Seconds"))
        self.range_combo_box.addItem("30 " + self.tr("Seconds"))
        self.range_combo_box.addItem("60 " + self.tr("Seconds"))
        self.range_combo_box.setCurrentIndex(0)

        self.tab_widget.setTabText(0, self.tr("Information"))
        self.tab_widget.setTabText(1, self.tr("Graphs"))
        self.tab_widget.setTabText(2, self.tr("Log"))
        self.tab_widget.setTabText(3, self.tr("Actions"))

        self.stop_push_button.setText(self.tr("Stop Node"))
        self.restart_push_button.setText(self.tr("Restart Node"))
        self.stop_push_button.setEnabled(False)
        self.restart_push_button.setEnabled(False)

        self.selected_label.setText(self.tr("Selected") + ":")
        self.range_label.setText(self.tr("Range") + ":")
        
        self.log_tab_tree_view.setRootIsDecorated(False)
        self.log_tab_tree_view.setAlternatingRowColors(True)
        self.log_tab_tree_view.setSortingEnabled(True)
        self.log_tab_tree_view.sortByColumn(1, Qt.AscendingOrder)

        self.set_selected_item(self.__selected_item)
        self.__model.layoutChanged.connect(self.update)

        self.__state = "ok"
        self.__previous_state = "ok"

        self.__deleted = False
        
        self.__timer = Timer(Duration(secs=2), self.update_graphs)
        

    def __del__(self):
        self.__deleted = True

    def connect_slots(self):
        """
        Connects the slots.
        """
        # : tab_widget
        self.tab_widget.currentChanged.connect(self.__on_current_tab_changed)
        #: restart_push_button
        self.restart_push_button.clicked.connect(self.__on_restart_push_button_clicked)
        #: stop_push_button
        self.stop_push_button.clicked.connect(self.__on_stop_push_button_clicked)
        #: start_push_button
        #self.start_push_button.clicked.connect(self.__on_start_push_button_clicked)
        #: range_combo_box
        self.range_combo_box.currentIndexChanged.connect(self.__on_range_combo_box_index_changed)


    def set_selected_item(self, index):
        """
        Sets the selected item.

        :param index: the index of the selected item
        :type selected_item: QModelIndex
        """
        if index is not None:
            src_index = index.model().mapToSource(index)
            self.__selected_item = src_index.internalPointer()
            self.__log_filter_proxy.filter_by_item(self.__selected_item)
            if self.__selected_item is not None:
                if self.__selected_item.can_execute_actions():
                    self.stop_push_button.setEnabled(True)
                    self.restart_push_button.setEnabled(True)
                else:
                    self.stop_push_button.setEnabled(False)
                    self.restart_push_button.setEnabled(False)
            self.update()


    def __on_current_tab_changed(self, tab):
        """
        Will be called when switching between tabs.

        :param tab: index of the current tab
        :type tab: int
        """
        if tab is 1:
            self.__draw_graphs = True
        else:
            self.__draw_graphs = False


    def __on_restart_push_button_clicked(self):
        """
        Handels the restart button and restarts a host or node.
        """
        if self.__selected_item is not None:
            self.__selected_item.execute_action("restart")


    def __on_stop_push_button_clicked(self):
        """Handels the stop button and stops a host or node."""
        if self.__selected_item is not None:
            self.__selected_item.execute_action("stop")


    def __on_range_combo_box_index_changed(self, index):
        """
        Handels the change of the graph range.

        :param index: the index of the selected range
        :type index: int
        """
        self.__current_combo_box_index = index


    def update_graphs(self, event):
        """
        Updates the graph plot.
        """
        pass
      
    
    def update(self):
        """
        Updates the widget.
        """
        if not self.__deleted:

            if self.__selected_item is not None:
                data_dict = self.__selected_item.get_latest_data()
                self.__state = data_dict["state"]

                if self.__previous_state is not self.__state:
                    self.__previous_state = self.__state
                    if self.__state == "ok":
                        self.current_status_label.setText(self.tr("online"))
                        self.host_node_label.setText(self.tr("Current Status: Ok"))
                        pixmap = QPixmap(os.path.join(self.rp.get_path('rqt_arni_gui_detail'), 'resources/graphics',
                                                      'block_green.png'))
                    elif self.__state == "warning":
                        self.current_status_label.setText(self.tr("online"))
                        self.host_node_label.setText(self.tr("Current Status: Warning"))
                        pixmap = QPixmap(os.path.join(self.rp.get_path('rqt_arni_gui_detail'), 'resources/graphics',
                                                      'block_orange.png'))
                    elif self.__state == "unknown":
                        self.current_status_label.setText(self.tr("unkown"))
                        self.host_node_label.setText(self.tr("Current Status: Unkown"))
                        pixmap = QPixmap(os.path.join(self.rp.get_path('rqt_arni_gui_detail'), 'resources/graphics',
                                                      'block_grey.png'))
                    else:
                        self.host_node_label.setText(self.tr("Current Status: Error"))
                        pixmap = QPixmap(os.path.join(self.rp.get_path('rqt_arni_gui_detail'), 'resources/graphics',
                                                      'block_red.png'))
                    self.status_light_label.setPixmap(pixmap)
                content = self.__selected_item.get_detailed_data()

                scroll_value = self.information_tab_text_browser.verticalScrollBar().value()
                self.information_tab_text_browser.setHtml(content)
                self.information_tab_text_browser.verticalScrollBar().setSliderPosition(scroll_value)
            else:
                self.host_node_label.setText(self.tr("No item selected"))
                self.current_status_label.setText(self.tr("Offline"))
                self.information_tab_text_browser.setText(self.tr("Please select an item in the TreeView to get more information"
                                                          " about it"))


    def __combo_box_index_to_seconds(self, index):
        """
        Calculates the range from the combo-box index.
        
        :param index: the index of teh combo-box
        :type index: int
        
        :returns: the seconds of the selected index 
        :rtype: int
        """
        if self.__current_combo_box_index == 0:
            return 10
        elif self.__current_combo_box_index == 1:
            return 30
        else:
            return 300


    def get_current_tab(self):
        """
        Returns the current tab.
        
        :returns: the current tab 
        :rtype: int
        """
        return self.tab_widget.currentIndex()


    def set_current_tab(self, index=0):
        """
        Sets the default tab.
        
        :param index: the index of the tab
        :type index: int
        """
        if index is None:
            index = 0
        self.tab_widget.setCurrentIndex(index)


    def get_range_combo_box_index(self):
        """
        Returns the index of the combo-box.
        
        :returns: the index
        :rtype: int
        """
        return self.range_combo_box.currentIndex()


    def set_range_combo_box_index(self, index=0):
        """
        Sets the default value of the combo-box.
        
        :param index: the index of the combo-box
        :type index: int
        """
        if index is None:
            index = 0
        self.range_combo_box.setCurrentIndex(index)