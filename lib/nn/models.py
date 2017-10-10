from lasagne.layers import InputLayer, ReshapeLayer, NonlinearityLayer, ExpressionLayer
from lasagne.layers import ElemwiseSumLayer, ElemwiseMergeLayer
from lasagne.lasagne import DenseLayer
from lasagne.layers.dnn import BatchNormDNNLayer
from lasagne.nonlinearities import rectify, softmax

from lib.nn.layers import SharedDotLayer, SPTNormReshapeLayer


def build_classification_model(clouds, norms, config):
    steps = config.get('steps')
    n_f = config.get('n_f')
    features = config.get('input_features')

    KDNet = {}
    if features == 'no':
        KDNet['input'] = InputLayer((None, 1, 2**steps), input_var=clouds)
    else:
        KDNet['input'] = InputLayer((None, 3, 2**steps), input_var=clouds)

    for i in xrange(steps):
        KDNet['norm{}_r'.format(i+1)] = InputLayer((None, 3, 2**(c_steps-1-i)), input_var=norms[i])
        KDNet['norm{}_l'.format(i+1)] = ExpressionLayer(KDNet['norm{}_r'.format(i+1)], lambda X: -X)

        KDNet['norm{}_l_X-'.format(i+1)] = SPTNormReshapeLayer(KDNet['norm{}_l'.format(i+1)], '-', 0, n_f[i+1])
        KDNet['norm{}_l_Y-'.format(i+1)] = SPTNormReshapeLayer(KDNet['norm{}_l'.format(i+1)], '-', 1, n_f[i+1])
        KDNet['norm{}_l_Z-'.format(i+1)] = SPTNormReshapeLayer(KDNet['norm{}_l'.format(i+1)], '-', 2, n_f[i+1])
        KDNet['norm{}_l_X+'.format(i+1)] = SPTNormReshapeLayer(KDNet['norm{}_l'.format(i+1)], '+', 0, n_f[i+1])
        KDNet['norm{}_l_Y+'.format(i+1)] = SPTNormReshapeLayer(KDNet['norm{}_l'.format(i+1)], '+', 1, n_f[i+1])
        KDNet['norm{}_l_Z+'.format(i+1)] = SPTNormReshapeLayer(KDNet['norm{}_l'.format(i+1)], '+', 2, n_f[i+1])
    
        KDNet['norm{}_r_X-'.format(i+1)] = SPTNormReshapeLayer(KDNet['norm{}_r'.format(i+1)], '-', 0, n_f[i+1])
        KDNet['norm{}_r_Y-'.format(i+1)] = SPTNormReshapeLayer(KDNet['norm{}_r'.format(i+1)], '-', 1, n_f[i+1])
        KDNet['norm{}_r_Z-'.format(i+1)] = SPTNormReshapeLayer(KDNet['norm{}_r'.format(i+1)], '-', 2, n_f[i+1])
        KDNet['norm{}_r_X+'.format(i+1)] = SPTNormReshapeLayer(KDNet['norm{}_r'.format(i+1)], '+', 0, n_f[i+1])
        KDNet['norm{}_r_Y+'.format(i+1)] = SPTNormReshapeLayer(KDNet['norm{}_r'.format(i+1)], '+', 1, n_f[i+1])
        KDNet['norm{}_r_Z+'.format(i+1)] = SPTNormReshapeLayer(KDNet['norm{}_r'.format(i+1)], '+', 2, n_f[i+1])

        KDNet['cloud{}'.format(i+1)] = SharedDotLayer(KDNet['input'], n_f[i]) if i == 0 else \
                                        ElemwiseSumLayer([KDNet['cloud{}_l_X-_masked'.format(i)],
                                                          KDNet['cloud{}_l_Y-_masked'.format(i)],
                                                          KDNet['cloud{}_l_Z-_masked'.format(i)],
                                                          KDNet['cloud{}_l_X+_masked'.format(i)],
                                                          KDNet['cloud{}_l_Y+_masked'.format(i)],
                                                          KDNet['cloud{}_l_Z+_masked'.format(i)],
                                                          KDNet['cloud{}_r_X-_masked'.format(i)],
                                                          KDNet['cloud{}_r_Y-_masked'.format(i)],
                                                          KDNet['cloud{}_r_Z-_masked'.format(i)],
                                                          KDNet['cloud{}_r_X+_masked'.format(i)],
                                                          KDNet['cloud{}_r_Y+_masked'.format(i)],
                                                          KDNet['cloud{}_r_Z+_masked'.format(i)]])
        KDNet['cloud{}_bn'.format(i+1)] = BatchNormDNNLayer(KDNet['cloud{}'.format(i+1)])
        KDNet['cloud{}_relu'.format(i+1)] = NonlinearityLayer(KDNet['cloud{}_bn'.format(i+1)], rectify)

        KDNet['cloud{}_r'.format(i+1)] = ExpressionLayer(KDNet['cloud{}_relu'.format(i+1)],
                                                          lambda X: X[:, :, 1::2], (None, n_f[i], 2**(steps - i - 1)))
        KDNet['cloud{}_l'.format(i+1)] = ExpressionLayer(KDNet['cloud{}_relu'.format(i+1)],
                                                          lambda X: X[:, :, ::2], (None, n_f[i], 2**(steps - i - 1)))
        
        KDNet['cloud{}_l_X-'.format(i+1)] = SharedDotLayer(KDNet['cloud{}_l'.format(i+1)], n_f[i+1])
        KDNet['cloud{}_l_Y-'.format(i+1)] = SharedDotLayer(KDNet['cloud{}_l'.format(i+1)], n_f[i+1])
        KDNet['cloud{}_l_Z-'.format(i+1)] = SharedDotLayer(KDNet['cloud{}_l'.format(i+1)], n_f[i+1])
        KDNet['cloud{}_l_X+'.format(i+1)] = SharedDotLayer(KDNet['cloud{}_l'.format(i+1)], n_f[i+1])
        KDNet['cloud{}_l_Y+'.format(i+1)] = SharedDotLayer(KDNet['cloud{}_l'.format(i+1)], n_f[i+1])
        KDNet['cloud{}_l_Z+'.format(i+1)] = SharedDotLayer(KDNet['cloud{}_l'.format(i+1)], n_f[i+1])
        
        KDNet['cloud{}_r_X-'.format(i+1)] = SharedDotLayer(KDNet['cloud{}_r'.format(i+1)], n_f[i+1],
                                                           W=KDNet['cloud{}_l_X-'.format(i+1)].W, 
                                                           b=KDNet['cloud{}_l_X-'.format(i+1)].b)
        KDNet['cloud{}_r_Y-'.format(i+1)] = SharedDotLayer(KDNet['cloud{}_r'.format(i+1)], n_f[i+1],
                                                           W=KDNet['cloud{}_l_Y-'.format(i+1)].W, 
                                                           b=KDNet['cloud{}_l_Y-'.format(i+1)].b)
        KDNet['cloud{}_r_Z-'.format(i+1)] = SharedDotLayer(KDNet['cloud{}_r'.format(i+1)], n_f[i+1],
                                                           W=KDNet['cloud{}_l_Z-'.format(i+1)].W, 
                                                           b=KDNet['cloud{}_l_Z-'.format(i+1)].b)
        KDNet['cloud{}_r_X+'.format(i+1)] = SharedDotLayer(KDNet['cloud{}_r'.format(i+1)], n_f[i+1],
                                                           W=KDNet['cloud{}_l_X+'.format(i+1)].W,
                                                           b=KDNet['cloud{}_l_X+'.format(i+1)].b)
        KDNet['cloud{}_r_Y+'.format(i+1)] = SharedDotLayer(KDNet['cloud{}_r'.format(i+1)], n_f[i+1],
                                                           W=KDNet['cloud{}_l_Y+'.format(i+1)].W,
                                                           b=KDNet['cloud{}_l_Y+'.format(i+1)].b)
        KDNet['cloud{}_r_Z+'.format(i+1)] = SharedDotLayer(KDNet['cloud{}_r'.format(i+1)], n_f[i+1],
                                                           W=KDNet['cloud{}_l_Z+'.format(i+1)].W,
                                                           b=KDNet['cloud{}_l_Z+'.format(i+1)].b)

        KDNet['cloud{}_l_X-_masked'.format(i+1)] = ElemwiseMergeLayer([KDNet['cloud{}_l_X-'.format(i+1)],
                                                                        KDNet['norm{}_l_X-'.format(i+1)]], T.mul)
        KDNet['cloud{}_l_Y-_masked'.format(i+1)] = ElemwiseMergeLayer([KDNet['cloud{}_l_Y-'.format(i+1)],
                                                                        KDNet['norm{}_l_Y-'.format(i+1)]], T.mul)
        KDNet['cloud{}_l_Z-_masked'.format(i+1)] = ElemwiseMergeLayer([KDNet['cloud{}_l_Z-'.format(i+1)],
                                                                        KDNet['norm{}_l_Z-'.format(i+1)]], T.mul)
        KDNet['cloud{}_l_X+_masked'.format(i+1)] = ElemwiseMergeLayer([KDNet['cloud{}_l_X+'.format(i+1)],
                                                                        KDNet['norm{}_l_X+'.format(i+1)]], T.mul)
        KDNet['cloud{}_l_Y+_masked'.format(i+1)] = ElemwiseMergeLayer([KDNet['cloud{}_l_Y+'.format(i+1)],
                                                                        KDNet['norm{}_l_Y+'.format(i+1)]], T.mul)
        KDNet['cloud{}_l_Z+_masked'.format(i+1)] = ElemwiseMergeLayer([KDNet['cloud{}_l_Z+'.format(i+1)],
                                                                        KDNet['norm{}_l_Z+'.format(i+1)]], T.mul)
        KDNet['cloud{}_r_X-_masked'.format(i+1)] = ElemwiseMergeLayer([KDNet['cloud{}_r_X-'.format(i+1)],
                                                                        KDNet['norm{}_r_X-'.format(i+1)]], T.mul)
        KDNet['cloud{}_r_Y-_masked'.format(i+1)] = ElemwiseMergeLayer([KDNet['cloud{}_r_Y-'.format(i+1)],
                                                                        KDNet['norm{}_r_Y-'.format(i+1)]], T.mul)
        KDNet['cloud{}_r_Z-_masked'.format(i+1)] = ElemwiseMergeLayer([KDNet['cloud{}_r_Z-'.format(i+1)],
                                                                        KDNet['norm{}_r_Z-'.format(i+1)]], T.mul)
        KDNet['cloud{}_r_X+_masked'.format(i+1)] = ElemwiseMergeLayer([KDNet['cloud{}_r_X+'.format(i+1)],
                                                                        KDNet['norm{}_r_X+'.format(i+1)]], T.mul)
        KDNet['cloud{}_r_Y+_masked'.format(i+1)] = ElemwiseMergeLayer([KDNet['cloud{}_r_Y+'.format(i+1)],
                                                                        KDNet['norm{}_r_Y+'.format(i+1)]], T.mul)
        KDNet['cloud{}_r_Z+_masked'.format(i+1)] = ElemwiseMergeLayer([KDNet['cloud{}_r_Z+'.format(i+1)],
                                                                        KDNet['norm{}_r_Z+'.format(i+1)]], T.mul)

    KDNet['cloud_fin'] = ElemwiseSumLayer([KDNet['cloud{}_l_X-_masked'.format(steps)],
                                           KDNet['cloud{}_l_Y-_masked'.format(steps)],
                                           KDNet['cloud{}_l_Z-_masked'.format(steps)],
                                           KDNet['cloud{}_l_X+_masked'.format(steps)],
                                           KDNet['cloud{}_l_Y+_masked'.format(steps)],
                                           KDNet['cloud{}_l_Z+_masked'.format(steps)],
                                           KDNet['cloud{}_r_X-_masked'.format(steps)],
                                           KDNet['cloud{}_r_Y-_masked'.format(steps)],
                                           KDNet['cloud{}_r_Z-_masked'.format(steps)],
                                           KDNet['cloud{}_r_X+_masked'.format(steps)],
                                           KDNet['cloud{}_r_Y+_masked'.format(steps)],
                                           KDNet['cloud{}_r_Z+_masked'.format(steps)]])
    KDNet['cloud_fin_bn'] = BatchNormDNNLayer(KDNet['cloud_fin'])
    KDNet['cloud_fin_relu'] = NonlinearityLayer(KDNet['cloud_fin_bn'], rectify)
    KDNet['cloud_fin_reshape'] = ReshapeLayer(KDNet['cloud_fin_relu'], (-1, n_f[-1]))
    KDNet['output'] = DenseLayer(KDNet['cloud_fin_reshape'], 10, nonlinearity=softmax)

    return KDNet