import pandas as pd
import tensorflow as tf

import numpy as np
import tensorflow as tf
import tensorflow_recommenders as tfrs


# Build a model.
class RankingModel(tf.keras.Model):
    def __init__(self, unique_userIds, unique_productIds):
        super().__init__()
        embedding_dimension = 32

        self.user_embeddings = tf.keras.Sequential(
            [
                tf.keras.layers.experimental.preprocessing.StringLookup(
                    vocabulary=unique_userIds, mask_token=None
                ),
                # add addional embedding to account for unknow tokens
                tf.keras.layers.Embedding(len(unique_userIds) + 1, embedding_dimension),
            ]
        )

        self.product_embeddings = tf.keras.Sequential(
            [
                tf.keras.layers.experimental.preprocessing.StringLookup(
                    vocabulary=unique_productIds, mask_token=None
                ),
                # add addional embedding to account for unknow tokens
                tf.keras.layers.Embedding(
                    len(unique_productIds) + 1, embedding_dimension
                ),
            ]
        )
        # Set up a retrieval task and evaluation metrics over the
        # entire dataset of candidates.
        self.ratings = tf.keras.Sequential(
            [
                tf.keras.layers.Dense(256, activation="relu"),
                tf.keras.layers.Dense(64, activation="relu"),
                tf.keras.layers.Dense(1),
            ]
        )

    def call(self, userId, productId):
        user_embeddings = self.user_embeddings(userId)
        product_embeddings = self.product_embeddings(productId)
        return self.ratings(tf.concat([user_embeddings, product_embeddings], axis=1))


# Build a model.
class amazonModel(tfrs.models.Model):
    def __init__(self, unique_userIds, unique_productIds):
        super().__init__()
        self.ranking_model: tf.keras.Model = RankingModel(
            unique_userIds, unique_productIds
        )
        self.task: tf.keras.layers.Layer = tfrs.tasks.Ranking(
            loss=tf.keras.losses.MeanSquaredError(),
            metrics=[tf.keras.metrics.RootMeanSquaredError()],
        )

    def compute_loss(self, features, training=False):
        rating_predictions = self.ranking_model(
            features["userId"], features["productId"]
        )

        return self.task(labels=features["rating"], predictions=rating_predictions)


# Esta función devuelve una lista de productos recomendados para un usuario.
# p_usuario: el usuario para el que se van a recomendar productos.

def recomendar_producto(p_usuario):
    electronics_data = pd.read_csv(
        "ratings_Electronics (1).csv",
        dtype={"rating": "int8"},
        names=["userId", "productId", "rating", "timestamp"],
        index_col=None,
        header=0,
    )
    print(electronics_data.head())

    electronics_data.describe()["rating"].reset_index()

    # Check for missing values
    pd.DataFrame(electronics_data.isnull().sum().reset_index()).rename(
        columns={0: "Total missing", "index": "Columns"}
    )

    data_by_date = electronics_data.copy()
    data_by_date.timestamp = pd.to_datetime(
        electronics_data.timestamp, unit="s"
    )  # .dt.date
    data_by_date = data_by_date.sort_values(
        by="timestamp", ascending=False
    ).reset_index(drop=True)
    print("**Number of Ratings each day:**")
    data_by_date.groupby("timestamp")["rating"].count().tail(10).reset_index()

    data_by_date["year"] = data_by_date.timestamp.dt.year
    data_by_date["month"] = data_by_date.timestamp.dt.month
    rating_by_year = (
        data_by_date.groupby(["year", "month"])["rating"].count().reset_index()
    )
    rating_by_year["date"] = pd.to_datetime(
        rating_by_year["year"].astype("str")
        + "-"
        + rating_by_year["month"].astype("str")
        + "-1"
    )
    rating_by_year.plot(x="date", y="rating")

    cutoff_no_rat = 50  ## Only count products which received more than or equal 50
    cutoff_year = 2011  ## Only count Rating after 2011
    recent_data = data_by_date.loc[data_by_date["year"] > cutoff_year]
    print("Number of Rating: {:,}".format(recent_data.shape[0]))
    print("Number of Users: {:,}".format(len(recent_data.userId.unique())))
    print("Number of Products: {:,}".format(len(recent_data.productId.unique())))
    del data_by_date  ### Free up memory ###
    recent_prod = (
        recent_data.loc[
            recent_data.groupby("productId")["rating"]
            .transform("count")
            .ge(cutoff_no_rat)
        ]
        .reset_index(drop=True)
        .drop(["timestamp", "year", "month"], axis=1)
    )
    del recent_data  ### Free up memory ###

    userIds = recent_prod.userId.unique()
    productIds = recent_prod.productId.unique()
    total_ratings = len(recent_prod.index)

    ratings = tf.data.Dataset.from_tensor_slices(
        {
            "userId": tf.cast(recent_prod.userId.values, tf.string),
            "productId": tf.cast(recent_prod.productId.values, tf.string),
            "rating": tf.cast(
                recent_prod.rating.values,
                tf.int8,
            ),
        }
    )

    tf.random.set_seed(42)
    shuffled = ratings.shuffle(100_000, seed=42, reshuffle_each_iteration=False)

    # Split the ratings DataFrame into training and test DataFrames
    train = shuffled.take(int(total_ratings * 0.8))
    test = shuffled.skip(int(total_ratings * 0.8)).take(int(total_ratings * 0.2))

    unique_productIds = productIds
    unique_userIds = userIds

    model = amazonModel(unique_userIds, unique_productIds)
    model.compile(optimizer=tf.keras.optimizers.Adagrad(learning_rate=0.1))
    cached_train = train.shuffle(100_000).batch(8192).cache()
    cached_test = test.batch(4096).cache()
    model.fit(cached_train, epochs=10)

    # Evaluate.
    model.evaluate(cached_test, return_dict=True)

    user_rand = next((user for user in userIds if user == p_usuario), None)
    test_rating = {}
    for m in test.take(5):
        test_rating[m["productId"].numpy()] = RankingModel(
            unique_userIds, unique_productIds
        )(tf.convert_to_tensor([user_rand]), tf.convert_to_tensor([m["productId"]]))

    print("Top 5 recommended products for User {}: ".format(user_rand))
    recommended_products = []
    for m in sorted(test_rating, key=test_rating.get, reverse=True):
        product_name = m.decode()
        recommended_products.append(product_name)
        print(product_name)

    return recommended_products


if __name__ == "__main__":
    p_usuario = "A32PYU1S3Y7QFY"
    recomendar_producto(p_usuario)
