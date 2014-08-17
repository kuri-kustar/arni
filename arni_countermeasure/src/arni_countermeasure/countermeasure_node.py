from constraint_handler import *
from rated_statistic_storage import *
import rospy
from arni_msgs.msg import RatedStatistics
from arni_core.host_lookup import *
import helper
import time

class CountermeasureNode(object):

    """A ROS node.
    Evaluates incoming rated statistics with a list of constraints.
    If those constraints turn out to be true appropriate action is taken.
    """

    def __init__(self):
        """Periodically (threading)
        evaluate the constraints and clean old statistics."""
        super(CountermeasureNode, self).__init__()

        self.__init_params()

        rospy.init_node("countermeasure_node", log_level=rospy.DEBUG)

        #: The storage of all incoming rated statistic.
        self.__rated_statistic_storage = RatedStatisticStorage()

        #: The handler for all constraints.
        self.__constraint_handler = ConstraintHandler(
            self.__rated_statistic_storage)

        #: The time to wait between two evaluations.
        self.__evaluation_period = helper.get_param_duration(
            helper.ARNI_CTM_CFG_NS + "evaluation_period")

        self.__register_subscriber()

    def __register_subscriber(self):
        """Register to the rated statistics."""
        rospy.Subscriber(
            "/statistics_rated", RatedStatistics,
            self.__rated_statistic_storage.callback_rated_statistic)
        rospy.Subscriber(
            "/statistics_rated", RatedStatistics,
            HostLookup().callback_rated)

    def loop(self):
        # simulation? wait for begin
        while rospy.Time.now() == rospy.Time(0):
            time.sleep(0.01)
        while not rospy.is_shutdown():
            self.__constraint_handler.evaluate_constraints()
            self.__constraint_handler.execute_reactions()

            rospy.sleep(self.__evaluation_period)

    def __init_params(self):
        """Initializes params on the parameter server,
        if they are not already set.
        """

        default = {
            "reaction_autonomy_level": 100,
            "storage_timeout": 10,
            "evaluation_period": 0.2,
            "default/min_reaction_interval": 10,
            "default/reaction_timeout": 30
        }
        for param in default:
            if not rospy.has_param(helper.ARNI_CTM_CFG_NS + param):
                rospy.set_param(helper.ARNI_CTM_CFG_NS + param, default[param])


def main():
    try:
        cn = CountermeasureNode()
    #    rospy.loginfo(rospy.get_caller_id() + ": im on ")

        cn.loop()
    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
