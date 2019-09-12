import torch
import torch.nn.functional as F

from .basemodel import BaseModel
from ..layers import FM, AFMLayer


class AFM(BaseModel):

    def __init__(self,
                 linear_feature_columns, dnn_feature_columns, embedding_size=8, use_attention=True, attention_factor=8,
                 l2_reg_linear=1e-5, l2_reg_embedding=1e-5, l2_reg_att=1e-5, afm_dropout=0, init_std=0.0001, seed=1024,
                 task='binary', device='cpu'):
        """Instantiates the Attentional Factorization Machine architecture.
        :param linear_feature_columns: An iterable containing all the features used by linear part of the model.
        :param dnn_feature_columns: An iterable containing all the features used by deep part of the model.
        :param embedding_size: positive integer,sparse feature embedding_size
        :param use_attention: bool,whether use attention or not,if set to ``False``.it is the same as **standard Factorization Machine**
        :param attention_factor: positive integer,units in attention net
        :param l2_reg_linear: float. L2 regularizer strength applied to linear part
        :param l2_reg_embedding: float. L2 regularizer strength applied to embedding vector
        :param l2_reg_att: float. L2 regularizer strength applied to attention net
        :param afm_dropout: float in [0,1), Fraction of the attention net output units to dropout.
        :param init_std: float,to use as the initialize std of embedding vector
        :param seed: integer ,to use as random seed.
        :param task: str, ``"binary"`` for  binary logloss or  ``"regression"`` for regression loss
        :param device
        :return: A PyTorch model instance.
        """

        super(AFM, self).__init__(linear_feature_columns, dnn_feature_columns, embedding_size=embedding_size,
                                  dnn_hidden_units=[],
                                  l2_reg_linear=l2_reg_linear,
                                  l2_reg_embedding=l2_reg_embedding, l2_reg_dnn=0, init_std=init_std,
                                  seed=seed,
                                  dnn_dropout=0, dnn_activation=F.relu,
                                  task=task, device=device)

        self.use_attention = use_attention

        if use_attention:
            self.fm = AFMLayer(embedding_size, attention_factor, l2_reg_att, afm_dropout,
                               seed, device)
            self.add_regularization_loss(self._modules['fm'].weight, l2_reg_att)
        else:
            self.fm = FM()

        self.to(device)

    def forward(self, X):

        sparse_embedding_list, dense_value_list = self.input_from_feature_columns(X, self.dnn_feature_columns,
                                                                                  self.embedding_dict)
        logit = self.linear_model(X)
        if self.use_attention:
            logit += self.fm(sparse_embedding_list)
        else:
            logit += self.fm(torch.cat(sparse_embedding_list, dim=1))

        y_pred = self.out(logit)

        return y_pred
