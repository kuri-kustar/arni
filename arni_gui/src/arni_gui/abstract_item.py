from rospy.rostime import Duration, Time
from python_qt_binding.QtCore import QObject

import time as tm

# from ros_model import ROSModel

class AbstractItem(QObject):
    """ Provides a unified interface to access the items of the model
        INTERNAL: WARNING! Whenever the key-values at the beginning are not set right, the oddest things may occur!
    """

    def __init__(self, seuid, parent=QObject(), *args):
        #todo:doku is missing here
        """Initializes theAbstractItem

        :param parent: the parent-object
        :type parent: object
        """
        super(AbstractItem, self).__init__(parent)

        self.__data = {}
        self.__child_items = []
        self.__parent = parent
        self.seuid = seuid
        self.__type = "type"
        self._attributes = ['type', 'name', 'state', 'data', 'window_end']
        self._attributes.extend(args)

        self.__last_update = Time.now()

        # for item in self.__attributes:
        #     self.__add_data_list(item)
        #
        # for item in args:
        #     self.__add_data_list(item)


    def get_seuid(self):
        return self.seuid

    def get_state(self):
        return self.__data["state"][-1]


    def _add_data_list(self, name):
        self.__data[name] = []

    def append_child(self, child):
        """Append a child to the list of childs

        :param child: the child item
        :type child: AbstractItem
        """
        self.__child_items.append(child)

    def append_data_dict(self, data):
        """Append data to the data of the AbstractItem.

        :param data: the data to append in key value form
        :type data: dict
        """
        if "window_end" not in data:
            data["window_end"] = Time.now()
        for attribute in self._attributes:
            if attribute in data:
                self.__data[attribute].append(data[attribute])
            else:
                #todo: is there something better than None in this case? like "" ?
                self.__data[attribute].append(None)

        self.__update_current_state()

    def __update_current_state(self):
        length = len(self.__data["state"])
        #print("__update_current_state")
        for i in range(length - len(
                (self.get_items_younger_than(self.__last_update, "window_end", "state"))["window_end"]), length):
            if self.__data["state"][i] == "error":
                self.__data["state"][-1] = "warning"
                break
        self.__last_update = Time.now()

    def append_data(self, data):
        """Append data to the data of the AbstractItem.

        :param data: the data to append in key value form
        :type data:
        """
        for attribute in self._attributes:
            #todo: correct?
            try:
                self.__data[attribute].append(data.getattr(attribute, None))
            except KeyError:
                print("KeyError occurred when trying to access %s", attribute)
                raise
        self.__update_current_state()


    def update_data(self, data, window_start, window_end):
        """

        :param data:
        :type data:
        :param time:
        :type time: rostime?
        :return:
        """
        found = False
        #todo: are these all bad cases?
        for current in range(0, len(self.__data["window_start"])):
            if window_end < self.__data[window_start][current]:
                continue
            if window_start > self.__data[window_end][current]:
                continue
            found = True
            for attribute in self._attributes:
                self.__data[attribute][current] = data.getattr(attribute, None)

                # for key in data:
                #     self.__data[key][current] = data[key]

        if found is not True:
            raise UserWarning("No matching time window was found. Could not update the AbstractItem")
        self.__update_current_state()


    def child_count(self):
        sum = 0
        for item in self.__child_items:
            sum += 1
            sum += item.child_count()

        return sum
        #return len(self.child_items)


    def column_count(self):
        # todo: return !not! a concrete number here ?!?!
        return 4

    def get_childs(self):
        """

        :return:
        """
        return self.__child_items


    def get_child(self, row):
        """Returns the child at the position row

        :param row: the index of the row
        :type row: int

        :returns: AbstractItem
        """
        return self.__child_items[row]


    def row(self):
        """
        todo: document!
        """
        if self.__parent:
            return self.__parent.childItems.index(self)

        return 0


    def get_latest_data(self, *kwargs):
        #todo:update docu, now more mighty
        """Returns the latest dict of the data_list or the item of the dict with the given key

        :param kwargs: the keys to the dict
        :type kwargs: str
        :returns: dict or the item
        """
        if kwargs is not None:
            for key in kwargs:
                if key is 'name':
                    return self.seuid
                elif key is 'type':
                    return self.__type
                else:
                    try:
                        return self.__data[key][-1]
                    except KeyError:
                        print("KeyError caught when accessing element %s.", key)
                        raise

        return_dict = {}
        # return dict of latest item
        for entry in self.__data:
            return_dict[entry] = self.__data[entry][-1]
        return return_dict


    def parent(self):
        """Returns the parent of this or None if there is no parent

        :returns: AbstractItem
        """
        return self.__parent

    #todo: what are the following 3 methods for and how can they be done better?
    def get_items_older_than(self, time):
        """Returns all items which are older than time

        :param time: the upper bound in seconds
        :type time: rospy.Time

        :returns: dict of lists
        """
        return_values = []
        for key in self.__data:
            return_values[key] = []

        list_of_time = self.__data["window_end"]
        for i in range(0, len(list_of_time)):
            # check timestamp
            #end_time = Time.now() - Duration(nsecs=time)
            if list_of_time[i] < time:
                #return_values.append()
                for key in self.__data:
                    return_values[key].append(self.__data[key][i])
        return return_values


    def delete_items_older_than(self, time):
        """Deletes all items which are older than time

        :param time: the upper bound
        :type time: rospy.Time
        """
        list_of_time = self.__data["window_end"]
        for i in range(0, len(list_of_time)):
            # check timestamp
            #end_time = Time.now() - Duration(nsecs=time)
            if list_of_time[i] < time:
                #return_values.append()
                for key in self.__data:
                    del self.__data[key][i]


    def get_items_younger_than(self, time, *args):
        """Returns all items which are younger than time

        :param time: the lower bound in seconds
        :type time: rospy.Time
 
        :returns: dict of lists
        """
        #todo: method assumes the data comes in sorted by time. if this is not the case, this method will not work!
        #print("info" + " AbstractItem" + " duration of time:" + str(int(str(Time.now() - time))/1000000) + " milliseconds")
        #now = Time.now()
        return_values = {}
        #todo: adapt to args
        for key in self.__data:
            return_values[key] = []
        breakpoint = 0

        list_of_time = self.__data["window_end"]
        #print(len(list_of_time))
        #print("first time: " + tm.strftime("%d.%m-%H:%M:%S", tm.localtime((int(str(self.__data["window_end"][0]))/1000000000))))
        #print("last time: " + tm.strftime("%d.%m-%H:%M:%S", tm.localtime((int(str(self.__data["window_end"][-1]))/1000000000))))
        #print("for")
        for i in range(len(list_of_time) - 1, -1, -1):
            #print(i)
            #print(len(list_of_time))
            #print(int(str(list_of_time[i]))-int(str(time)))
            if list_of_time[i] < time:
                breakpoint = i + 1
                # i + 1 was the first hit
                #print("entered")
                if args is None:
                    for key in self.__data:
                        try:
                            return_values[key] = self.__data[key][breakpoint:len(list_of_time)]
                            #print("i is " + str(i) +"length: " + str(len(return_values[key])) + " complete length: " + str(len(list_of_time)))
                        except IndexError:
                            print(
                            "IndexError! length of the list %s, accessed index %s. length of data at given point %s, key is %s",
                            len(list_of_time), i, len(self.__data[key]), key)
                            raise
                else:
                    for entry in args:
                        try:
                            #todo [i:len(list_of_time)] is this the right window?
                            return_values[entry] = self.__data[entry][breakpoint:len(list_of_time)]
                            #print("i is " + str(i) + "key: " + entry + " length: " + str(len(return_values[entry])) + " complete length: " + str(len(list_of_time)))
                        except IndexError:
                            print(
                            "IndexError! length of the list %s, accessed index %s. length of data at given point %s, key is %s",
                            len(list_of_time), i, len(self.__data[entry]), entry)
                            raise
                break

                            # now shrink the time itself
        #print("length time: " + str(len(return_values["window_end"])) + " length state: " + str(len(return_values["state"])))

        #print("length return values: " + str(len(return_values["window_end"])))
        return return_values



        # check timestamp
        #start_time = Time.now() - Duration(nsecs=time)
        # if list_of_time[i] > time:
        #     for key in self.__data:
        #         try:
        #             return_values[key].append(self.__data[key][i])
        #         except IndexError:
        #             print("IndexError! length of the list %s,assert(len(return_values) == len(return_values[""])) accessed index %s. length of data at given point %s, key is %s",
        #                   len(list_of_time), i, len(self.__data[key]), key)
        #             raise
        #print("info" + " AbstractItem" + " get_items_younger_than took: " + str(int(str(Time.now() - now))/1000000) + " milliseconds")
        return return_values

    def execute_action(self, action):
        """Executes a action on the current item like stop or restart. Calls to this method should be
        redirected to the remote host on executed there."""
        pass

    def get_detailed_data(self):
        """
        Returns detailed description of current state as html text.

        :return:
        """
        raise NotImplemented()

    def get_plotable_items(self):
        raise NotImplemented()