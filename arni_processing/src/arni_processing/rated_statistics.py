from arni_msgs.msg import RatedStatistics, RatedStatisticsEntity


class RatedStatisticsContainer:
    """
    Wraps the result of the comparison between the actual metadata and the specification.
    """

    def __init__(self, seuid):
        """
        Creates a new RatedStatisticsContainer object for the given connection identifier.

        :param seuid: Identifies a host/node/connection.
        :type seuid: str or message type
        """
        if not isinstance(seuid, str):
            self.__from_msg_type(seuid)
        self.seuid = seuid
        self.metatype = []
        self.actual = []
        self.expected = []
        self.state = []

    def add_value(self, metatype, actual, expected, state):
        """
        Adds a group of values for a metatype.

        :param metatype: The measured field.
        :type metatype: str.
        :param actual: The actual value.
        :param expected: The expected value.
        :param state: An error state based on the difference between actual and expected.
        """
        self.metatype.append(metatype)
        self.actual.append(actual)
        self.expected.append(expected)
        self.state.append(state)

    def keys(self):
        return self.metatype

    def __from_msg_type(self, msg):
        try:
            self.seuid = msg.seuid
            for re in msg.rated_statistics_entity:
                self.metatype.append(msg.statistic_type)
                self.actual.append(msg.actual_value)
                self.expected.append(msg.expected_value)
                self.state.append(msg.state)
        except TypeError:
            raise  TypeError("Could not access fields of a RatedStatistics.msg")

    def to_msg_type(self):
        """
        Creates a RatedStatisticsContainer messagetype based on the current data.

        :return: A RatedStatisticsContainer object from the current data.
        """
        r = RatedStatistics()
        r.seuid = self.seuid
        if self.seuid[0] == "h":
            r.host = self.seuid[2:]
        try:
            r.window_start = self.get_value("window_start")["actual"]
            r.window_stop = self.get_value("window_stop")["actual"]
        except KeyError:
            r.window_start = r.window_stop = None
        for k in self.keys():
            if k in ("host", "node", "node_sub", "node_pub", "topic"):
                continue
            re = RatedStatisticsEntity()
            re.statistic_type = k
            values = self.get_value(k)
            # actual_value
            try:
                for v in values["actual"]:
                    re.actual_value.append(str(v))
            except TypeError:
                re.actual_value.append(str(values["actual"]))
            # expected value
            try:
                for v in values["expected"]:
                    re.expected_value.append(" - ".join(str(x) for x in v))
            except TypeError:
                if values["expected"] is None:
                    re.expected_value.append("?")
                else:
                    re.expected_value.append(" - ".join(str(x) for x in values["expected"]))
            # state
            re.state = []
            try:
                for v in values["state"]:
                    re.state.append(v)
            except TypeError:
                re.state.append(values["state"])
            r.rated_statistics_entity.append(re)
        return r

    def get_value(self, metatype):
        """
        Returns values of the given metatype.

        :param metatype: The metatype to return the values for.
        :type metatype: str.
        :returns: A dictionary with the keys *metatype*, *actual*, *expected* and *state*, each field containing it's respective values.
        """
        if metatype in self.metatype:
            index = self.metatype.index(metatype)
            return {"metatype": metatype, "actual": self.actual[index], "expected": self.expected[index], "state": self.state[index] }
        else:
            return False