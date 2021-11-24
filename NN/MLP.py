"""
Implementation of the Multi Layer Perceptron.
"""
import time
import numpy as np
from layer import Layer, error

class MLP:
    """
    Multi Layer Perceptron class.
    """
    def __init__(self, structure, func, starting_points,
                    eta=0.1, lamb=0, norm_L=2, alpha=0, nesterov=False):
        """
        __init__ function of the class.

        Parameters
        ----------
        structure : list
            List containing the number of unit of each Layer in the MLP.
        func : list of tuple
            List that contains:
                [( act. func. name, func. params. ), ..., (...)]
            The number of elements (tuples) of this list is equal to the number
            of Layers of the MLP.
        eta : float
            The learning rate (default is 0.1)
        lamb : float
            The Tikhonov regularization factor (default is 0).
        norm_L : int
            The type of the norm for the Tikhonov regularization (default is 2,
            euclidean).
        alpha : int
            Momentum factor (to do).
        nesterov = False
            Implementing the nesterov momentum (to do).
        starting_point : list or numpy 1d array of float
            The starting weights of each layer (i) is initialized extracting
            from a random uniform distribution in the interval:
                [-starting_point[i], starting_point[i]]
        """
        self.structure=structure #numero di unità per ogni layer
        self.network=[]
        self.func=func #lista di tuple con (funzione, slope)
        self.starting_points=starting_points #lista degli start_point
        self.eta = eta
        self.lamb = lamb
        self.norm_L = norm_L
        self.alpha = alpha
        self.nesterov = nesterov

        self.error = []
        self.val_error = []
        self.epoch = 0



    def __getattr__(self,attr):
        """Get the atribute of MLP"""
        return [getattr(lay,attr) for lay in self.network]

    def train(self, input_data, labels, val_data, val_labels, epoch,
                clean_net = False):
        """
        Parameters
        ----------
        input_data : list or numpy 2d array
            Array with the data in input to the MLP.
        labels : list or numpy 2d array
            Labels of the input_data.
        epoch : int
            Number of epoch for training.
        val_data : list or numpy 2d array
            Array with the validation data in input to the MLP.
        val_labels : list or numpy 2d array
            Labels of the val_data.
        clean_net : boolean
            If True restore the net, if False keep the pretrained net (if exist)
        """
        # Check if all the input are numpy arrays
        input_data = np.array(input_data)
        labels = np.array(labels)
        val_data = np.array(val_data)
        val_labels = np.array(val_labels)

        # Reset the net if clean_net == True
        if clean_net:
            self.network = []
            self.error = []
            self.val_error = []
            self.epoch = 0

        # If the net is just an empty list fill it with the layers
        if len(self.network) == 0:
            self.create_net(input_data)

        # Start train the net
        total_time = 0
        real_start = time.time()
        print(f'Starting training {self.epoch} epoch', end = '\r')
        for i in range(epoch):
            start_loop = time.time()

            # Train dataset #
            self.network[0].input = input_data
            self.feedforward()
            self.learning_step(labels)
            self.error.append(error(labels,self.network[-1].out)/len(labels))

            # Validation dataset #
            self.network[0].input = val_data
            self.feedforward()
            self.val_error.append(error(val_labels,self.network[-1].out)/len(val_labels))

            # Printing the error
            string_val_err = f' --- [val error = {self.val_error[self.epoch]:.4f}]'
            string_err = f' --- [train error = {self.error[self.epoch]:.4f}]'
            string_err += string_val_err

            # Printing remaining time
            elapsed_for_this_loop = time.time()-start_loop
            total_time += elapsed_for_this_loop
            mean_for_loop = total_time/(i+1)
            remain_time = mean_for_loop*(epoch-i)
            string_time = f' --- [countdown : {remain_time:.1f} s]'
            print(f'Epoch {self.epoch}:' + string_err + string_time + ' '*10, end = '\r')

            # Updating epoch
            self.epoch += 1

        # Final print
        print(f'Epoch {self.epoch}:' + string_err + ' '*30, end = '\n')
        print(f'Elapsed time: {time.time()-real_start} s')

    def predict(self, data):
        """ Predict out for new data """
        self.network[0].input = data
        self.feedforward()
        return self.network[-1].out

    def create_net(self, input_data):
        """
        Feed the input of the net and propagate it

        Parameters
        ----------
        input_data : list or numpy 2d array
            Array with the data in input to the MLP.
        """
        for layer,num_unit in enumerate(self.structure):
            if layer==0:
                self.network.append(Layer(num_unit,input_data,func=self.func[layer],
                                          starting_points=self.starting_points[layer]))
            else:
                self.network.append(Layer(num_unit,self.network[layer-1].out, func=self.func[layer],
                                          starting_points=self.starting_points[layer]))

    def feedforward(self):
        """ Move the input to the output of the net"""
        for lay_prev,lay_next in zip(self.network[:-1:],self.network[1::]):
            lay_next.input=lay_prev.out

    def learning_step(self,labels):
        """
        Implementing the backpropagation.

        Parameters
        ----------
        labels : list or numpy 2d array
            Labels of the input_data.
        """
        for reverse_layer_number,layer in enumerate(self.network[::-1]):
            if reverse_layer_number==0:
                delta=((labels-layer.out)*layer.der_func(layer.net))
            else:
                delta=(np.matmul(delta,weight_1)*layer.der_func(layer.net))
            weight_1=layer.weight
            dW=np.sum([np.outer(i,j) for i,j in zip(delta,layer.input)], axis=0) #batch
            db=np.sum(delta,axis=0)

            layer.weight += self.eta*dW - self.norm_L * self.lamb * layer.weight**(self.norm_L-1 )
            layer.bias   += self.eta*db - self.norm_L * self.lamb * layer.bias**( self.norm_L-1 )