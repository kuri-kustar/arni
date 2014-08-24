from node_statistics_handler import NodeStatisticsHandler
import subprocess
import rosnode
import roslaunch
import psutil

class NodeManager(object):
    """ 
    Can restart or stop nodes or execute a countermeasure. 
    """
    
    def __init__(self):
        """
        empty comment to prevent indention error for whatever reason
        """    
           
    def stop_node(self, node_id):
        """
        Stops the node with the given id.
        Returns a message about operation's success.
        
        :param node_id: id of the node to be stopped.
        :type node_id: String.
        :returns: String
        """
        success, fail = rosnode.kill_nodes([node_id])
        if node_id in success:
            return 'Node %s successfully stopped'%node_id
        else:
            return 'Node %s could not be stopped'%node_id
            
        
    def restart_node(self, node):
        """
        Restarts a node with the given id.
        Returns a message about operation's success.
        
        :param node_id: id of the node to be restarted.
        :type node_id: NodeStatisticsHandler.
        :returns: String
        """
        """pipe = subprocess.Popen('ps -p %s -o cmd'%node.get_pid(),
                                                shell = True, stdout = subprocess.PIPE).stdout
                                out = pipe.read()
                        
                                path = out.split('/',6)
                                arguments = None
                                if len(path[6].split(' ')) == 1:
                                    package = path[5]
                                    exe = path[6]
                                elif len(path[6].split(' ')) > 1:
                                    package = path[5]
                                    exe = path[6].split(' ')[0]
                                    arguments = path[6].split(' ',1)[1]
                        
                                new_node = roslaunch.core.Node(package, exe, args = arguments)
                                self.stop_node(node.id)
                                
                                try:
                                    launch = roslaunch.scriptapi.ROSLaunch()
                                    launch.start()
                                    node_proc = launch.launch(new_node)
                        
                                    return 'Restarted Node' + node.id
                                except roslaunch.core.RLException:
                                    return 'failed to launch new Node'"""
        proc = node.node_proc
        cmd = proc.cmdline()
        if 'successfully' in self.stop_node(node.id):
            try:
                psutil.Popen(cmd)
                return 'Restarted %s'%node.id
            except OSError:
                return 'Failed to restart %s'%node.id
        else:
            return 'Node %s could not be stopped'%node.id


    def execute_command(self, args):
        """
        Executes a system call with the given arguments.
        Returns a message about operation's success.
        
        :param args: Arguments for the system call
        :type args: String
        :returns: String
        """
        
        try:
            proc = subprocess.Popen(args, stdout = subprocess.PIPE, 
                                stderr = subprocess.PIPE)
        
            output = proc.communicate()
            print output[0]
            proc.wait()
            if proc.poll() == 0:
                return 'command executed successfully'
            else:
                return output[1]
        except OSError:
            return 'Failed to execute command'
