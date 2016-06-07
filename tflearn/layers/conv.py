# -*- coding: utf-8 -*-
from __future__ import division, print_function, absolute_import

import tensorflow as tf

import tflearn
from .. import variables as vs
from .. import activations
from .. import initializations
from .. import losses
from .. import utils


def conv_2d(incoming, nb_filter, filter_size, strides=1, padding='same',
            activation='linear', bias=True, weights_init='uniform_scaling',
            bias_init='zeros', regularizer=None, weight_decay=0.001,
            trainable=True, restore=True, name="Conv2D"):
    """ Convolution 2D.

    Input:
        4-D Tensor [batch, height, width, in_channels].

    Output:
        4-D Tensor [batch, new height, new width, nb_filter].

    Arguments:
        incoming: `Tensor`. Incoming 4-D Tensor.
        nb_filter: `int`. The number of convolutional filters.
        filter_size: 'int` or list of `ints`. Size of filters.
        strides: 'int` or list of `ints`. Strides of conv operation.
            Default: [1 1 1 1].
        padding: `str` from `"same", "valid"`. Padding algo to use.
            Default: 'same'.
        activation: `str` (name) or `function` (returning a `Tensor`).
            Activation applied to this layer (see tflearn.activations).
            Default: 'linear'.
        bias: `bool`. If True, a bias is used.
        weights_init: `str` (name) or `Tensor`. Weights initialization.
            (see tflearn.initializations) Default: 'truncated_normal'.
        bias_init: `str` (name) or `Tensor`. Bias initialization.
            (see tflearn.initializations) Default: 'zeros'.
        regularizer: `str` (name) or `Tensor`. Add a regularizer to this
            layer weights (see tflearn.regularizers). Default: None.
        weight_decay: `float`. Regularizer decay parameter. Default: 0.001.
        trainable: `bool`. If True, weights will be trainable.
        restore: `bool`. If True, this layer weights will be restored when
            loading a model
        name: A name for this layer (optional). Default: 'Conv2D'.

    Attributes:
        scope: `Scope`. This layer scope.
        W: `Variable`. Variable representing filter weights.
        b: `Variable`. Variable representing biases.

    """
    assert padding in ['same', 'valid', 'SAME', 'VALID'], \
        "Padding must be same' or 'valid'"

    input_shape = utils.get_incoming_shape(incoming)
    assert len(input_shape) == 4, "Incoming Tensor shape must be 4-D"
    filter_size = utils.autoformat_filter_conv2d(filter_size,
                                                 input_shape[-1],
                                                 nb_filter)
    strides = utils.autoformat_kernel_2d(strides)
    padding = utils.autoformat_padding(padding)

    with tf.name_scope(name) as scope:

        W_init = weights_init
        if isinstance(weights_init, str):
            W_init = initializations.get(weights_init)()
        W_regul = None
        if regularizer:
            W_regul = lambda x: losses.get(regularizer)(x, weight_decay)
        W = vs.variable(scope + 'W', shape=filter_size,
                        regularizer=W_regul, initializer=W_init,
                        trainable=trainable, restore=restore)
        # Track per layer variables
        tf.add_to_collection(tf.GraphKeys.LAYER_VARIABLES + '/' + scope, W)

        b = None
        if bias:
            b_init = initializations.get(bias_init)()
            b = vs.variable(scope + 'b', shape=nb_filter,
                            initializer=b_init, trainable=trainable,
                            restore=restore)
            # Track per layer variables
            tf.add_to_collection(tf.GraphKeys.LAYER_VARIABLES + '/' + scope, b)

        inference = tf.nn.conv2d(incoming, W, strides, padding)
        if b: inference = tf.nn.bias_add(inference, b)

        if isinstance(activation, str):
            inference = activations.get(activation)(inference)
        elif hasattr(activation, '__call__'):
            inference = activation(inference)
        else:
            raise ValueError("Invalid Activation.")

        # Track activations.
        tf.add_to_collection(tf.GraphKeys.ACTIVATIONS, inference)

    # Add attributes to Tensor to easy access weights.
    inference.scope = scope
    inference.W = W
    inference.b = b

    return inference


def conv_2d_transpose(incoming, nb_filter, filter_size, output_shape,
                      strides=1, padding='same', activation='linear',
                      bias=True, weights_init='uniform_scaling',
                      bias_init='zeros', regularizer=None, weight_decay=0.001,
                      trainable=True, restore=True, name="Conv2DTranspose"):

    """ Convolution 2D Transpose.

    This operation is sometimes called "deconvolution" after (Deconvolutional
    Networks)[http://www.matthewzeiler.com/pubs/cvpr2010/cvpr2010.pdf], but is
    actually the transpose (gradient) of `conv2d` rather than an actual
    deconvolution.

    Input:
        4-D Tensor [batch, height, width, in_channels].

    Output:
        4-D Tensor [batch, new height, new width, nb_filter].

    Arguments:
        incoming: `Tensor`. Incoming 4-D Tensor.
        nb_filter: `int`. The number of convolutional filters.
        filter_size: `int` or list of `ints`. Size of filters.
        output_shape: `list of ints`. Dimensions of the output tensor.
            Can optionally include the number of conv filters.
            [new height, new width, nb_filter] or [new height, new width].
        strides: `int` or list of `ints`. Strides of conv operation.
            Default: [1 1 1 1].
        padding: `str` from `"same", "valid"`. Padding algo to use.
            Default: 'same'.
        activation: `str` (name) or `function` (returning a `Tensor`).
            Activation applied to this layer (see tflearn.activations).
            Default: 'linear'.
        bias: `bool`. If True, a bias is used.
        weights_init: `str` (name) or `Tensor`. Weights initialization.
            (see tflearn.initializations) Default: 'truncated_normal'.
        bias_init: `str` (name) or `Tensor`. Bias initialization.
            (see tflearn.initializations) Default: 'zeros'.
        regularizer: `str` (name) or `Tensor`. Add a regularizer to this
            layer weights (see tflearn.regularizers). Default: None.
        weight_decay: `float`. Regularizer decay parameter. Default: 0.001.
        trainable: `bool`. If True, weights will be trainable.
        restore: `bool`. If True, this layer weights will be restored when
            loading a model
        name: A name for this layer (optional). Default: 'Conv2DTranspose'.

    Attributes:
        scope: `Scope`. This layer scope.
        W: `Variable`. Variable representing filter weights.
        b: `Variable`. Variable representing biases.

    """
    assert padding in ['same', 'valid', 'SAME', 'VALID'], \
        "Padding must be same' or 'valid'"

    input_shape = utils.get_incoming_shape(incoming)
    assert len(input_shape) == 4, "Incoming Tensor shape must be 4-D"

    filter_size = utils.autoformat_filter_conv2d(filter_size,
                                                 nb_filter,
                                                 input_shape[-1])
    strides = utils.autoformat_kernel_2d(strides)
    padding = utils.autoformat_padding(padding)

    with tf.name_scope(name) as scope:

        W_init = initializations.get(weights_init)()
        W_regul = None
        if regularizer:
            W_regul = lambda x: losses.get(regularizer)(x, weight_decay)
        W = vs.variable(scope + 'W', shape=filter_size,
                        regularizer=W_regul, initializer=W_init,
                        trainable=trainable, restore=restore)
        # Track per layer variables
        tf.add_to_collection(tf.GraphKeys.LAYER_VARIABLES + '/' + scope, W)

        b = None
        if bias:
            b_init = initializations.get(bias_init)()
            b = vs.variable(scope + 'b', shape=nb_filter,
                            initializer=b_init, trainable=trainable,
                            restore=restore)
            # Track per layer variables
            tf.add_to_collection(tf.GraphKeys.LAYER_VARIABLES + '/' + scope, b)

        # Determine the complete shape of the output tensor.
        batch_size = tf.gather(tf.shape(incoming), tf.constant([0]))
        if len(output_shape) == 2:
            output_shape = output_shape + [nb_filter]
        elif len(output_shape) != 3:
            raise Exception("output_shape length error: " 
                            + str(len(output_shape))
                            + ", only a length of 2 or 3 is supported.")
        complete_out_shape = tf.concat(0, [batch_size, tf.constant(output_shape)])
 
        inference = tf.nn.conv2d_transpose(incoming, W, complete_out_shape,
                                           strides, padding)
        
        # Reshape tensor so its shape is correct.
        inference.set_shape([None] + output_shape)

        if b: inference = tf.nn.bias_add(inference, b)

        if isinstance(activation, str):
            inference = activations.get(activation)(inference)
        elif hasattr(activation, '__call__'):
            inference = activation(inference)
        else:
            raise ValueError("Invalid Activation.")

        # Track activations.
        tf.add_to_collection(tf.GraphKeys.ACTIVATIONS, inference)

    # Add attributes to Tensor to easy access weights.
    inference.scope = scope
    inference.W = W
    inference.b = b

    return inference


def upsample_2d(incoming, kernel_size, name="UpSample2D"):
    """ UpSample 2D.

    Input:
        4-D Tensor [batch, height, width, in_channels].

    Output:
        4-D Tensor [batch, pooled height, pooled width, in_channels].

    Arguments:
        incoming: `Tensor`. Incoming 4-D Layer to upsample.
        kernel_size: 'int` or list of `ints`. Upsampling kernel size.
        name: A name for this layer (optional). Default: 'UpSample2D'.

    Attributes:
        scope: `Scope`. This layer scope.

    """
    input_shape = utils.get_incoming_shape(incoming)
    assert len(input_shape) == 4, "Incoming Tensor shape must be 4-D"
    kernel = utils.autoformat_kernel_2d(kernel_size)

    with tf.name_scope(name) as scope:
        inference = tf.image.resize_nearest_neighbor(
            incoming, size=input_shape[1:3] * tf.constant(kernel[1:3]))
        inference.set_shape((None, input_shape[1] * kernel[1],
                            input_shape[2] * kernel[2], None))

    # Add attributes to Tensor to easy access weights
    inference.scope = scope

    return inference


def max_pool_2d(incoming, kernel_size, strides=None, padding='same',
                name="MaxPool2D"):
    """ Max Pooling 2D.

    Input:
        4-D Tensor [batch, height, width, in_channels].

    Output:
        4-D Tensor [batch, pooled height, pooled width, in_channels].

    Arguments:
        incoming: `Tensor`. Incoming 4-D Layer.
        kernel_size: 'int` or list of `ints`. Pooling kernel size.
        strides: 'int` or list of `ints`. Strides of conv operation.
            Default: same as kernel_size.
        padding: `str` from `"same", "valid"`. Padding algo to use.
            Default: 'same'.
        name: A name for this layer (optional). Default: 'MaxPool2D'.

    Attributes:
        scope: `Scope`. This layer scope.

    """
    assert padding in ['same', 'valid', 'SAME', 'VALID'], \
        "Padding must be same' or 'valid'"

    input_shape = utils.get_incoming_shape(incoming)
    assert len(input_shape) == 4, "Incoming Tensor shape must be 4-D"

    kernel = utils.autoformat_kernel_2d(kernel_size)
    strides = utils.autoformat_kernel_2d(strides) if strides else kernel
    padding = utils.autoformat_padding(padding)

    with tf.name_scope(name) as scope:
        inference = tf.nn.max_pool(incoming, kernel, strides, padding)

        # Track activations.
        tf.add_to_collection(tf.GraphKeys.ACTIVATIONS, inference)

    # Add attributes to Tensor to easy access weights
    inference.scope = scope

    return inference


def avg_pool_2d(incoming, kernel_size, strides=None, padding='same',
                name="AvgPool2D"):
    """ Average Pooling 2D.

    Input:
        4-D Tensor [batch, height, width, in_channels].

    Output:
        4-D Tensor [batch, pooled height, pooled width, in_channels].

    Arguments:
        incoming: `Tensor`. Incoming 4-D Layer.
        kernel_size: 'int` or list of `ints`. Pooling kernel size.
        strides: 'int` or list of `ints`. Strides of conv operation.
            Default: same as kernel_size.
        padding: `str` from `"same", "valid"`. Padding algo to use.
            Default: 'same'.
        name: A name for this layer (optional). Default: 'AvgPool2D'.

    Attributes:
        scope: `Scope`. This layer scope.

    """
    assert padding in ['same', 'valid', 'SAME', 'VALID'], \
        "Padding must be same' or 'valid'"

    input_shape = utils.get_incoming_shape(incoming)
    assert len(input_shape) == 4, "Incoming Tensor shape must be 4-D"

    kernel = utils.autoformat_kernel_2d(kernel_size)
    strides = utils.autoformat_kernel_2d(strides) if strides else kernel
    padding = utils.autoformat_padding(padding)

    with tf.name_scope(name) as scope:
        inference = tf.nn.avg_pool(incoming, kernel, strides, padding)

        # Track activations.
        tf.add_to_collection(tf.GraphKeys.ACTIVATIONS, inference)

    # Add attributes to Tensor to easy access weights
    inference.scope = scope

    return inference


def conv_1d(incoming, nb_filter, filter_size, strides=1, padding='same',
            activation='linear', bias=True, weights_init='uniform_scaling',
            bias_init='zeros', regularizer=None, weight_decay=0.001,
            trainable=True, restore=True, name="Conv1D"):
    """ Convolution 1D.

    Input:
        3-D Tensor [batch, steps, in_channels].

    Output:
        3-D Tensor [batch, new steps, nb_filters].

    Arguments:
        incoming: `Tensor`. Incoming 3-D Tensor.
        nb_filter: `int`. The number of convolutional filters.
        filter_size: 'int` or list of `ints`. Size of filters.
        strides: 'int` or list of `ints`. Strides of conv operation.
            Default: [1 1 1 1].
        padding: `str` from `"same", "valid"`. Padding algo to use.
            Default: 'same'.
        activation: `str` (name) or `function` (returning a `Tensor`).
            Activation applied to this layer (see tflearn.activations).
            Default: 'linear'.
        bias: `bool`. If True, a bias is used.
        weights_init: `str` (name) or `Tensor`. Weights initialization.
            (see tflearn.initializations) Default: 'truncated_normal'.
        bias_init: `str` (name) or `Tensor`. Bias initialization.
            (see tflearn.initializations) Default: 'zeros'.
        regularizer: `str` (name) or `Tensor`. Add a regularizer to this
            layer weights (see tflearn.regularizers). Default: None.
        weight_decay: `float`. Regularizer decay parameter. Default: 0.001.
        trainable: `bool`. If True, weights will be trainable.
        restore: `bool`. If True, this layer weights will be restored when
            loading a model
        name: A name for this layer (optional). Default: 'Conv1D'.

    Attributes:
        scope: `Scope`. This layer scope.
        W: `Variable`. Variable representing filter weights.
        b: `Variable`. Variable representing biases.

    """
    assert padding in ['same', 'valid', 'SAME', 'VALID'], \
        "Padding must be same' or 'valid'"

    input_shape = utils.get_incoming_shape(incoming)
    assert len(input_shape) == 3, "Incoming Tensor shape must be 3-D"
    filter_size = utils.autoformat_filter_conv2d(filter_size,
                                                 input_shape[-1],
                                                 nb_filter)
    # filter_size = [1, filter_size[1], 1, 1]
    filter_size[1] = 1
    strides = utils.autoformat_kernel_2d(strides)
    # strides = [1, strides[1], 1, 1]
    strides[1] = 1
    padding = utils.autoformat_padding(padding)

    with tf.name_scope(name) as scope:

        W_init = initializations.get(weights_init)()
        W_regul = None
        if regularizer:
            W_regul = lambda x: losses.get(regularizer)(x, weight_decay)
        W = vs.variable(scope + 'W', shape=filter_size,
                        regularizer=W_regul, initializer=W_init,
                        trainable=trainable, restore=restore)
        # Track per layer variables
        tf.add_to_collection(tf.GraphKeys.LAYER_VARIABLES + '/' + scope, W)

        b = None
        if bias:
            b_init = initializations.get(bias_init)()
            b = vs.variable(scope + 'b', shape=nb_filter,
                            initializer=b_init, trainable=trainable,
                            restore=restore)
            # Track per layer variables
            tf.add_to_collection(tf.GraphKeys.LAYER_VARIABLES + '/' + scope, b)

        # Adding dummy dimension to fit with Tensorflow conv2d
        inference = tf.expand_dims(incoming, 2)
        inference = tf.nn.conv2d(inference, W, strides, padding)
        if b: inference = tf.nn.bias_add(inference, b)
        inference = tf.squeeze(inference, [2])

        if isinstance(activation, str):
            inference = activations.get(activation)(inference)
        elif hasattr(activation, '__call__'):
            inference = activation(inference)
        else:
            raise ValueError("Invalid Activation.")

        # Track activations.
        tf.add_to_collection(tf.GraphKeys.ACTIVATIONS, inference)

    # Add attributes to Tensor to easy access weights.
    inference.scope = scope
    inference.W = W
    inference.b = b

    return inference


def max_pool_1d(incoming, kernel_size, strides=None, padding='same',
                name="MaxPool1D"):
    """ Max Pooling 1D.

    Input:
        3-D Tensor [batch, steps, in_channels].

    Output:
        3-D Tensor [batch, pooled steps, in_channels].

    Arguments:
        incoming: `Tensor`. Incoming 3-D Layer.
        kernel_size: 'int` or list of `ints`. Pooling kernel size.
        strides: 'int` or list of `ints`. Strides of conv operation.
            Default: same as kernel_size.
        padding: `str` from `"same", "valid"`. Padding algo to use.
            Default: 'same'.
        name: A name for this layer (optional). Default: 'MaxPool1D'.

    Attributes:
        scope: `Scope`. This layer scope.

    """
    assert padding in ['same', 'valid', 'SAME', 'VALID'], \
        "Padding must be same' or 'valid'"

    input_shape = utils.get_incoming_shape(incoming)
    assert len(input_shape) == 3, "Incoming Tensor shape must be 3-D"

    kernel = utils.autoformat_kernel_2d(kernel_size)
    kernel = [1, kernel[1], 1, 1]
    strides = utils.autoformat_kernel_2d(strides) if strides else kernel
    strides = [1, strides[1], 1, 1]
    padding = utils.autoformat_padding(padding)

    with tf.name_scope(name) as scope:
        inference = tf.expand_dims(incoming, 2)
        inference = tf.nn.max_pool(inference, kernel, strides, padding)
        inference = tf.squeeze(inference, [2])

        # Track activations.
        tf.add_to_collection(tf.GraphKeys.ACTIVATIONS, inference)

    # Add attributes to Tensor to easy access weights
    inference.scope = scope

    return inference


def avg_pool_1d(incoming, kernel_size, strides=None, padding='same',
                name="AvgPool1D"):
    """ Average Pooling 1D.

    Input:
        3-D Tensor [batch, steps, in_channels].

    Output:
        3-D Tensor [batch, pooled steps, in_channels].

    Arguments:
        incoming: `Tensor`. Incoming 3-D Layer.
        kernel_size: 'int` or list of `ints`. Pooling kernel size.
        strides: 'int` or list of `ints`. Strides of conv operation.
            Default: same as kernel_size.
        padding: `str` from `"same", "valid"`. Padding algo to use.
            Default: 'same'.
        name: A name for this layer (optional). Default: 'AvgPool1D'.

    Attributes:
        scope: `Scope`. This layer scope.

    """
    assert padding in ['same', 'valid', 'SAME', 'VALID'], \
        "Padding must be same' or 'valid'"

    input_shape = utils.get_incoming_shape(incoming)
    assert len(input_shape) == 3, "Incoming Tensor shape must be 3-D"

    kernel = utils.autoformat_kernel_2d(kernel_size)
    kernel = [1, kernel[1], 1, 1]
    strides = utils.autoformat_kernel_2d(strides) if strides else kernel
    padding = utils.autoformat_padding(padding)

    with tf.name_scope(name) as scope:
        inference = tf.expand_dims(incoming, 2)
        inference = tf.nn.avg_pool(inference, kernel, strides, padding)
        inference = tf.squeeze(inference, [2])

        # Track activations.
        tf.add_to_collection(tf.GraphKeys.ACTIVATIONS, inference)

    # Add attributes to Tensor to easy access weights
    inference.scope = scope

    return inference


def global_avg_pool(incoming, name="GlobalAvgPool"):
    """ Global Average Pooling.

    Input:
        4-D Tensor [batch, height, width, in_channels].

    Output:
        2-D Tensor [batch, pooled dim]

    Arguments:
        incoming: `Tensor`. Incoming 4-D Tensor.
        name: A name for this layer (optional). Default: 'GlobalAvgPool'.

    """
    input_shape = utils.get_incoming_shape(incoming)
    assert len(input_shape) == 4, "Incoming Tensor shape must be 4-D"

    with tf.name_scope(name):
        return tf.reduce_mean(incoming, [1, 2])


def residual_block(incoming, nb_blocks, out_channels, downsample=False,
                   downsample_strides=2, activation='relu', batch_norm=True,
                   bias=True, weights_init='variance_scaling',
                   bias_init='zeros', regularizer='L2', weight_decay=0.0001,
                   trainable=True, restore=True, name="ResidualBlock"):
    """ Residual Block.

    A residual block as described in MSRA's Deep Residual Network paper.
    Full pre-activation architecture is used here.

    Input:
        4-D Tensor [batch, height, width, in_channels].

    Output:
        4-D Tensor [batch, new height, new width, nb_filter].

    Arguments:
        incoming: `Tensor`. Incoming 4-D Layer.
        nb_blocks: `int`. Number of layer blocks.
        out_channels: `int`. The number of convolutional filters of the
            convolution layers.
        downsample: `bool`. If True, apply downsampling using
            'downsample_strides' for strides.
        downsample_strides: `int`. The strides to use when downsampling.
        activation: `str` (name) or `function` (returning a `Tensor`).
            Activation applied to this layer (see tflearn.activations).
            Default: 'linear'.
        batch_norm: `bool`. If True, apply batch normalization.
        bias: `bool`. If True, a bias is used.
        weights_init: `str` (name) or `Tensor`. Weights initialization.
            (see tflearn.initializations) Default: 'uniform_scaling'.
        bias_init: `str` (name) or `tf.Tensor`. Bias initialization.
            (see tflearn.initializations) Default: 'zeros'.
        regularizer: `str` (name) or `Tensor`. Add a regularizer to this
            layer weights (see tflearn.regularizers). Default: None.
        weight_decay: `float`. Regularizer decay parameter. Default: 0.001.
        trainable: `bool`. If True, weights will be trainable.
        restore: `bool`. If True, this layer weights will be restored when
            loading a model
        name: A name for this layer (optional). Default: 'ShallowBottleneck'.

    References:
        - Deep Residual Learning for Image Recognition. Kaiming He, Xiangyu
            Zhang, Shaoqing Ren, Jian Sun. 2015.
        - Identity Mappings in Deep Residual Networks. Kaiming He, Xiangyu
            Zhang, Shaoqing Ren, Jian Sun. 2015.

    Links:
        - [http://arxiv.org/pdf/1512.03385v1.pdf]
            (http://arxiv.org/pdf/1512.03385v1.pdf)
        - [Identity Mappings in Deep Residual Networks]
            (https://arxiv.org/pdf/1603.05027v2.pdf)

    """
    resnet = incoming
    in_channels = incoming.get_shape().as_list()[-1]

    with tf.name_scope(name):
        for i in range(nb_blocks):

            identity = resnet

            if not downsample:
                downsample_strides = 1

            if batch_norm:
                resnet = tflearn.batch_normalization(resnet)
            resnet = tflearn.activation(resnet, activation)

            resnet = conv_2d(resnet, out_channels, 3,
                             downsample_strides, 'same', 'linear',
                             bias, weights_init, bias_init,
                             regularizer, weight_decay, trainable,
                             restore)

            if batch_norm:
                resnet = tflearn.batch_normalization(resnet)
            resnet = tflearn.activation(resnet, activation)

            resnet = conv_2d(resnet, out_channels, 3, 1, 'same',
                             'linear', bias, weights_init,
                             bias_init, regularizer, weight_decay,
                             trainable, restore)

            # Downsampling
            if downsample_strides > 1:
                identity = tflearn.avg_pool_2d(identity, 1,
                                               downsample_strides)

            # Projection to new dimension
            if in_channels != out_channels:
                ch = (out_channels - in_channels)//2
                identity = tf.pad(identity,
                                  [[0, 0], [0, 0], [0, 0], [ch, ch]])
                in_channels = out_channels

            resnet = resnet + identity

    return resnet


def residual_bottleneck(incoming, nb_blocks, bottleneck_size, out_channels,
                        downsample=False, downsample_strides=2,
                        activation='relu', batch_norm=True, bias=True,
                        weights_init='variance_scaling', bias_init='zeros',
                        regularizer='L2', weight_decay=0.0001,
                        trainable=True, restore=True, name="ResidualBottleneck"):
    """ Residual Bottleneck.

    A residual bottleneck block as described in MSRA's Deep Residual Network
    paper. Full pre-activation architecture is used here.

    Input:
        4-D Tensor [batch, height, width, in_channels].

    Output:
        4-D Tensor [batch, new height, new width, nb_filter].

    Arguments:
        incoming: `Tensor`. Incoming 4-D Layer.
        nb_blocks: `int`. Number of layer blocks.
        bottleneck_size: `int`. The number of convolutional filter of the
            bottleneck convolutional layer.
        out_channels: `int`. The number of convolutional filters of the
            layers surrounding the bottleneck layer.
        downsample: `bool`. If True, apply downsampling using
            'downsample_strides' for strides.
        downsample_strides: `int`. The strides to use when downsampling.
        activation: `str` (name) or `function` (returning a `Tensor`).
            Activation applied to this layer (see tflearn.activations).
            Default: 'linear'.
        batch_norm: `bool`. If True, apply batch normalization.
        bias: `bool`. If True, a bias is used.
        weights_init: `str` (name) or `Tensor`. Weights initialization.
            (see tflearn.initializations) Default: 'uniform_scaling'.
        bias_init: `str` (name) or `tf.Tensor`. Bias initialization.
            (see tflearn.initializations) Default: 'zeros'.
        regularizer: `str` (name) or `Tensor`. Add a regularizer to this
            layer weights (see tflearn.regularizers). Default: None.
        weight_decay: `float`. Regularizer decay parameter. Default: 0.001.
        trainable: `bool`. If True, weights will be trainable.
        restore: `bool`. If True, this layer weights will be restored when
            loading a model
        name: A name for this layer (optional). Default: 'DeepBottleneck'.

    References:
        - Deep Residual Learning for Image Recognition. Kaiming He, Xiangyu
            Zhang, Shaoqing Ren, Jian Sun. 2015.
        - Identity Mappings in Deep Residual Networks. Kaiming He, Xiangyu
            Zhang, Shaoqing Ren, Jian Sun. 2015.

    Links:
        - [http://arxiv.org/pdf/1512.03385v1.pdf]
            (http://arxiv.org/pdf/1512.03385v1.pdf)
        - [Identity Mappings in Deep Residual Networks]
            (https://arxiv.org/pdf/1603.05027v2.pdf)

    """
    resnet = incoming
    in_channels = incoming.get_shape().as_list()[-1]

    with tf.name_scope(name):
        for i in range(nb_blocks):

            identity = resnet

            if not downsample:
                downsample_strides = 1

            if batch_norm:
                resnet = tflearn.batch_normalization(resnet)
            resnet = tflearn.activation(resnet, activation)

            resnet = conv_2d(resnet, bottleneck_size, 1,
                             downsample_strides, 'valid',
                             'linear', bias, weights_init,
                             bias_init, regularizer, weight_decay,
                             trainable, restore)

            if batch_norm:
                resnet = tflearn.batch_normalization(resnet)
            resnet = tflearn.activation(resnet, activation)

            resnet = conv_2d(resnet, bottleneck_size, 3, 1, 'same',
                             'linear', bias, weights_init,
                             bias_init, regularizer, weight_decay,
                             trainable, restore)

            resnet = conv_2d(resnet, out_channels, 1, 1, 'valid',
                             activation, bias, weights_init,
                             bias_init, regularizer, weight_decay,
                             trainable, restore)

            # Downsampling
            if downsample_strides > 1:
                identity = tflearn.avg_pool_2d(identity, 1,
                                               downsample_strides)

            # Projection to new dimension
            if in_channels != out_channels:
                ch = (out_channels - in_channels)//2
                identity = tf.pad(identity,
                                  [[0, 0], [0, 0], [0, 0], [ch, ch]])
                in_channels = out_channels

                resnet = resnet + identity
                resnet = tflearn.activation(resnet, activation)

    return resnet


def highway_conv_2d(incoming, nb_filter, filter_size, strides=1, padding='same',
                    activation='linear', weights_init='uniform_scaling',
                    bias_init='zeros', regularizer=None, weight_decay=0.001,
                    trainable=True, restore=True, name="HighwayConv2D"):
    """ Highway Convolution 2D.

    Input:
        4-D Tensor [batch, height, width, in_channels].

    Output:
        4-D Tensor [batch, new height, new width, nb_filter].

    Arguments:
        incoming: `Tensor`. Incoming 4-D Tensor.
        nb_filter: `int`. The number of convolutional filters.
        filter_size: 'int` or list of `ints`. Size of filters.
        strides: 'int` or list of `ints`. Strides of conv operation.
            Default: [1 1 1 1].
        padding: `str` from `"same", "valid"`. Padding algo to use.
            Default: 'same'.
        activation: `str` (name) or `function` (returning a `Tensor`).
            Activation applied to this layer (see tflearn.activations).
            Default: 'linear'.
        weights_init: `str` (name) or `Tensor`. Weights initialization.
            (see tflearn.initializations) Default: 'truncated_normal'.
        bias_init: `str` (name) or `Tensor`. Bias initialization.
            (see tflearn.initializations) Default: 'zeros'.
        regularizer: `str` (name) or `Tensor`. Add a regularizer to this
            layer weights (see tflearn.regularizers). Default: None.
        weight_decay: `float`. Regularizer decay parameter. Default: 0.001.
        trainable: `bool`. If True, weights will be trainable.
        restore: `bool`. If True, this layer weights will be restored when
            loading a model
        name: A name for this layer (optional). Default: 'Conv2D'.

    Attributes:
        scope: `Scope`. This layer scope.
        W: `Variable`. Variable representing filter weights.
        W_T: `Variable`. Variable representing gate weights.
        b: `Variable`. Variable representing biases.
        b_T: `Variable`. Variable representing gate biases.

    """
    assert padding in ['same', 'valid', 'SAME', 'VALID'], \
        "Padding must be same' or 'valid'"

    input_shape = utils.get_incoming_shape(incoming)
    assert len(input_shape) == 4, "Incoming Tensor shape must be 4-D"
    filter_size = utils.autoformat_filter_conv2d(filter_size,
                                                 input_shape[-1],
                                                 nb_filter)
    strides = utils.autoformat_kernel_2d(strides)
    padding = utils.autoformat_padding(padding)

    with tf.name_scope(name) as scope:

        W_init = weights_init
        if isinstance(weights_init, str):
            W_init = initializations.get(weights_init)()
        W_regul = None
        if regularizer:
            W_regul = lambda x: losses.get(regularizer)(x, weight_decay)
        W = vs.variable(scope + 'W', shape=filter_size,
                        regularizer=W_regul, initializer=W_init,
                        trainable=trainable, restore=restore)
        # Track per layer variables
        tf.add_to_collection(tf.GraphKeys.LAYER_VARIABLES + '/' + scope, W)

        b_init = initializations.get(bias_init)()
        b = vs.variable(scope + 'b', shape=nb_filter,
                        initializer=b_init, trainable=trainable,
                        restore=restore)
        # Track per layer variables
        tf.add_to_collection(tf.GraphKeys.LAYER_VARIABLES + '/' + scope, b)

        # Weight and bias for the transform gate
        with tf.name_scope('transform_gate') as transform_gate:
            W_T = vs.variable(transform_gate + 'W', shape=nb_filter,
                              regularizer=None, initializer=W_init,
                              trainable=trainable, restore=restore)
            tf.add_to_collection(tf.GraphKeys.LAYER_VARIABLES + '/' +
                                 transform_gate, W_T)

            b_T = vs.variable(transform_gate + 'b', shape=nb_filter,
                              initializer=tf.constant_initializer(-1),
                              trainable=trainable, restore=restore)
            tf.add_to_collection(tf.GraphKeys.LAYER_VARIABLES + '/' +
                                 transform_gate, b_T)

        if isinstance(activation, str):
            activation = activations.get(activation)
        elif hasattr(activation, '__call__'):
            activation = activation
        else:
            raise ValueError("Invalid Activation.")

        # Shared convolution for gating
        convolved = tf.nn.conv2d(incoming, W, strides, padding)
        H = activation(convolved + b)
        T = tf.sigmoid(tf.mul(convolved, W_T) + b_T)
        C = tf.sub(1.0, T)
        inference = tf.add(tf.mul(H, T), tf.mul(convolved, C))

        # Track activations.
        tf.add_to_collection(tf.GraphKeys.ACTIVATIONS, inference)

    # Add attributes to Tensor to easy access weights.
    inference.scope = scope
    inference.W = W
    inference.W_T = W_T
    inference.b = b
    inference.b_T = b_T

    return inference


def highway_conv_1d(incoming, nb_filter, filter_size, strides=1, padding='same',
                    activation='linear', weights_init='uniform_scaling',
                    bias_init='zeros', regularizer=None, weight_decay=0.001,
                    trainable=True, restore=True, name="HighwayConv1D"):
    """ Highway Convolution 1D.

    Input:
        3-D Tensor [batch, steps, in_channels].

    Output:
        3-D Tensor [batch, new steps, nb_filters].

    Arguments:
        incoming: `Tensor`. Incoming 3-D Tensor.
        nb_filter: `int`. The number of convolutional filters.
        filter_size: 'int` or list of `ints`. Size of filters.
        strides: 'int` or list of `ints`. Strides of conv operation.
            Default: [1 1 1 1].
        padding: `str` from `"same", "valid"`. Padding algo to use.
            Default: 'same'.
        activation: `str` (name) or `function` (returning a `Tensor`).
            Activation applied to this layer (see tflearn.activations).
            Default: 'linear'.
        weights_init: `str` (name) or `Tensor`. Weights initialization.
            (see tflearn.initializations) Default: 'truncated_normal'.
        bias_init: `str` (name) or `Tensor`. Bias initialization.
            (see tflearn.initializations) Default: 'zeros'.
        regularizer: `str` (name) or `Tensor`. Add a regularizer to this
            layer weights (see tflearn.regularizers). Default: None.
        weight_decay: `float`. Regularizer decay parameter. Default: 0.001.
        trainable: `bool`. If True, weights will be trainable.
        restore: `bool`. If True, this layer weights will be restored when
            loading a model
        name: A name for this layer (optional). Default: 'HighwayConv1D'.

    Attributes:
        scope: `Scope`. This layer scope.
        W: `Variable`. Variable representing filter weights.
        W_T: `Variable`. Variable representing gate weights.
        b: `Variable`. Variable representing biases.
        b_T: `Variable`. Variable representing gate biases.

    """
    assert padding in ['same', 'valid', 'SAME', 'VALID'], \
        "Padding must be same' or 'valid'"

    input_shape = utils.get_incoming_shape(incoming)
    assert len(input_shape) == 3, "Incoming Tensor shape must be 3-D"
    filter_size = utils.autoformat_filter_conv2d(filter_size,
                                                 input_shape[-1],
                                                 nb_filter)
    # filter_size = [1, filter_size[1], 1, 1]
    filter_size[1] = 1
    strides = utils.autoformat_kernel_2d(strides)
    # strides = [1, strides[1], 1, 1]
    strides[1] = 1
    padding = utils.autoformat_padding(padding)

    with tf.name_scope(name) as scope:

        W_init = weights_init
        if isinstance(weights_init, str):
            W_init = initializations.get(weights_init)()
        W_regul = None
        if regularizer:
            W_regul = lambda x: losses.get(regularizer)(x, weight_decay)
        W = vs.variable(scope + 'W', shape=filter_size,
                        regularizer=W_regul, initializer=W_init,
                        trainable=trainable, restore=restore)
        # Track per layer variables
        tf.add_to_collection(tf.GraphKeys.LAYER_VARIABLES + '/' + scope, W)

        b_init = initializations.get(bias_init)()
        b = vs.variable(scope + 'b', shape=nb_filter,
                        initializer=b_init, trainable=trainable,
                        restore=restore)
        # Track per layer variables
        tf.add_to_collection(tf.GraphKeys.LAYER_VARIABLES + '/' + scope, b)

        # Weight and bias for the transform gate
        with tf.name_scope('transform_gate') as transform_gate:
            W_T = vs.variable(transform_gate + 'W', shape=nb_filter,
                            regularizer=None, initializer=W_init,
                            trainable=trainable, restore=restore)
            tf.add_to_collection(tf.GraphKeys.LAYER_VARIABLES + '/' +
                                 transform_gate, W_T)

            b_T = vs.variable(transform_gate + 'b', shape=nb_filter,
                              initializer=tf.constant_initializer(-1),
                              trainable=trainable, restore=restore)
            tf.add_to_collection(tf.GraphKeys.LAYER_VARIABLES + '/' +
                                 transform_gate, b_T)

        if isinstance(activation, str):
            activation = activations.get(activation)
        elif hasattr(activation, '__call__'):
            activation = activation
        else:
            raise ValueError("Invalid Activation.")

        # Adding dummy dimension to fit with Tensorflow conv2d
        inference = tf.expand_dims(incoming, 2)
        #shared convolution for gating
        convolved = tf.nn.conv2d(inference, W, strides, padding)
        H = activation(tf.squeeze(convolved + b, [2]))
        T = tf.sigmoid(tf.squeeze(tf.mul(convolved, W_T) + b_T, [2]))
        C = tf.sub(1.0, T)
        Q = tf.mul(H, T)
        R = tf.mul(tf.squeeze(convolved, [2]), C)
        inference = tf.add(Q, R)

        # Track activations.
        tf.add_to_collection(tf.GraphKeys.ACTIVATIONS, inference)

    # Add attributes to Tensor to easy access weights.
    inference.scope = scope
    inference.W = W
    inference.W_T = W_T
    inference.b = b
    inference.b_T = b_T

    return inference
