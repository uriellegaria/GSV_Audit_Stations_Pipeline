import docker
import tarfile
import os

class DockerContainerManagement:

    def __init__(self, imageName = "automaps_container"):
        self.imageName = imageName
        self.client = docker.from_env()
    
    def runNewContainer(self):
        '''
        Runs a container with the MaskRCNN image
        '''
        self.client.containers.run(self.imageName, detach = True, stdin_open = True, tty = True,)
    

    def getContainerName(self, index):
        '''
        Gets a container name from the list of available docker containers at the 
        specified index
        '''
        containerList = self.client.containers.list(all = True)
        if(index > len(containerList) - 1):
            print("Invalid index")
            return None
        
        container = containerList[index]
        containerName = container.name
        return containerName
    

    def getContainerId(self, index):
        '''
        Gets the container id of the container at a specified index from the list 
        of all available containers
        '''
        containerList = self.client.containers.list(all = True)
        if(index > len(containerList) - 1):
            print("Invalid index")
            return None
        
        container = containerList[index]
        containerId = container.id
        return containerId


    
    def stopContainer(self, containerName):
        container = self.client.containers.get(containerName)
        container.stop()

    def startContainer(self, containerName):
        #container = self.client.containers.run(self.imageName, name = containerName, stdin_open = True, tty = True, detach = True)
        container = self.client.containers.get(containerName)
        container.start()



    def putFileIntoContainer(self, src, dst, containerId):
        
        container = self.client.containers.get(containerId)
        currentDir = os.getcwd()
        os.chdir(os.path.dirname(src))
        srcName = os.path.basename(src)
        #print("src: "+srcName)
        tempTarName = "temp_tar.tar"
        #print("Building tar file")
        with tarfile.open(tempTarName, 'w') as tar:
            try:
                tar.add(srcName)
            
            finally:
                tar.close()
        
        with open(tempTarName, 'rb') as fd:
            okStatus = container.put_archive(path = dst, data = fd)
            if( not okStatus):
                raise Exception('Put file failed')
        
        os.chdir(currentDir)

    def runScript(self, containerId, pythonScriptLocation):
        container = self.client.containers.get(containerId)
        command = ["python3", pythonScriptLocation]
        code, resultString = container.exec_run(command)
        resultString = resultString.decode('utf-8')
        return resultString



    def getContainerFile(self, containerId, src, tarPath, dstPath):
        f = open(tarPath, 'wb')
        container = self.client.containers.get(containerId)

        bits, stat = container.get_archive(src)
        for chunk in bits:
            f.write(chunk)
        
        f.close()
    
        file = tarfile.open(tarPath) 
        file.extractall(dstPath) 
  
        file.close()

    
    def executeCommand(self, containerId, command):
        container = self.client.containers.get(containerId)
        code, resultString = container.exec_run(command)
        resultString = resultString.decode('utf-8')
        return resultString
    
    def listFilesInRoot(self, containerId):
        resultString = self.executeCommand(containerId, "ls /")
        return resultString
    