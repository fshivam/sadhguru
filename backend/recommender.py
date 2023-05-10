from sentence_transformers import SentenceTransformer, CrossEncoder
from backend.recommenders.youtube_recommender import YouTubeRecommender
from backend.recommenders.podcast_recommender import PodcastRecommender


class Recommender:
    def __init__(self, corpus_dict: dict):
        self.corpus_dict = corpus_dict
        self.encoder = SentenceTransformer("msmarco-distilbert-base-tas-b")
        self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.tracks = {
            "youtube": YouTubeRecommender(self.corpus_dict["youtube"]),
            "podcast": PodcastRecommender(self.corpus_dict["podcast"]),
        }

    def fit(self):
        for recommender in self.tracks.values():
            recommender.fit(encoder=self.encoder)

    def search(self, question: str, top_k: int) -> dict:
        results = [
            (
                track,
                recommender.search(
                    question=question,
                    encoder=self.encoder,
                    cross_encoder=self.cross_encoder,
                    top_k=top_k,
                ),
            )
            for track, recommender in self.tracks.items()
        ]
        results_dict = {
            track: {"hits": results[0], "recommendations": results[1]}
            for track, results in dict(results).items()
        }
        return results_dict

    def explore(self, query: str, top_k: int) -> dict:
        results = [
            (
                track,
                recommender.explore(query=query, encoder=self.encoder, top_k=top_k),
            )
            for track, recommender in self.tracks.items()
        ]
        results_dict = {
            track: {"hits": results[0], "recommendations": results[1]}
            for track, results in dict(results).items()
        }
        return results_dict


# class BaseRecommender:
#     def __init__(self):
#         self.encoder = SentenceTransformer("paraphrase-distilroberta-base-v1")
#         self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-electra-base")

#     def _encode(self, content: Union[List[str], str], verbosity: bool) -> torch.Tensor:
#         return self.encoder.encode(
#             content, convert_to_tensor=True, show_progress_bar=verbosity
#         )

#     def _semamtic_search(
#         self, query_embedding: torch.Tensor, corpus_str: str, top_k: int
#     ) -> List[dict]:
#         return util.semantic_search(
#             query_embedding, self.corpus_embeddings_dict[corpus_str], top_k=top_k
#         ).pop()

#     def fit(self, corpus: pd.DataFrame, columns: List[str], save_state: bool):
#         """
#         fit the corpuses to be used for recommendations
#         """
#         assert (
#             pd.Series(columns).isin(corpus.columns).all()
#         ), "columns to fit do not exist in the passed pd.DataFrame object"
#         self.corpus = corpus
#         self.corpus_embeddings_dict = {
#             column: self._encode(corpus[column].unique(), verbosity=True)
#             for column in columns
#         }
#         if save_state:
#             save_to_cache("recommender", self)

#     def search(
#         self, question: str, corpus: str, top_k: int
#     ) -> Tuple[pd.DataFrame, pd.DataFrame]:
#         pass

#     def explore(
#         self, query: str, corpus: List[str], top_k: int
#     ) -> Tuple[pd.DataFrame, pd.DataFrame]:
#         pass


# class YouTubeRecommender(BaseRecommender):
#     def __init__(self):
#         super(YouTubeRecommender, self).__init__()

#     def search(
#         self, question: str, corpus: str, top_k: int
#     ) -> Tuple[pd.DataFrame, pd.DataFrame]:
#         """
#         semantic search
#         """
#         assert (
#             corpus in self.corpus_embeddings_dict
#         ), f"Embeddings for [{corpus}] not found, please fit [{corpus}] first using the .fit() call"
#         question_embedding = self._encode(question, verbosity=False)
#         hits = self._semamtic_search(question_embedding, corpus, top_k)

#         # score all retrieved passages with the cross_encoder
#         cross_inp = [[question, self.corpus[corpus][hit["corpus_id"]]] for hit in hits]
#         cross_scores = self.cross_encoder.predict(cross_inp)

#         # sort results by the cross-encoder scores
#         for idx in range(len(cross_scores)):
#             hits[idx]["cross-score"] = cross_scores[idx]
#             hits[idx]["snippet"] = self.corpus[corpus][hits[idx]["corpus_id"]].replace(
#                 "\n", " "
#             )

#         # return hits and recommendations
#         hits = (
#             pd.DataFrame(hits)
#             .sort_values("cross-score", ascending=False)
#             .query("`cross-score` >= 0.0")
#         )
#         recommendations = hits.assign(
#             video_link=hits.corpus_id.apply(
#                 lambda x: f"https://www.youtube.com/watch?v={self.corpus.index.get_level_values(0)[x]}"
#             ),
#             snippet=hits.corpus_id.apply(lambda x: self.corpus.block.iloc[x]),
#             start=hits.corpus_id.apply(lambda x: self.corpus.start_time.iloc[x]),
#             end=hits.corpus_id.apply(lambda x: self.corpus.end_time.iloc[x]),
#         ).sort_values("start")
#         recommendations = (
#             recommendations.groupby("video_link", as_index=False)
#             .agg({"start": "min", "end": "max", "cross-score": "max"})
#             .sort_values("cross-score", ascending=False)
#         )
#         return (hits, recommendations)

#     def explore(
#         self, query: str, corpus: List[str], top_k: int
#     ) -> Tuple[pd.DataFrame, pd.DataFrame]:
#         assert all(corpus_str in self.corpus_embeddings_dict for corpus_str in corpus)
#         question_embedding = self._encode(query, verbosity=False)

#         # get hits
#         question_embedding = self._encode(query, verbosity=False)
#         hits = pd.concat(
#             [
#                 pd.DataFrame(
#                     self._semamtic_search(question_embedding, corpus_str, top_k=10)
#                 )
#                 for corpus_str in corpus
#             ],
#             axis=1,
#         )

#         # format hits
#         hits.columns = (" score ".join(corpus) + " score ").strip().split()
#         hits_corpus = pd.DataFrame(hits.loc[:, corpus].stack()).reset_index()
#         hits_score = pd.DataFrame(hits.loc[:, ["score"]].stack()).reset_index(drop=True)
#         hits = pd.concat([hits_corpus, hits_score], axis=1).drop(columns=["level_0"])
#         hits.columns = ["type", "corpus_id", "score"]
#         hits.sort_values("score", ascending=False, inplace=True)

#         # return hits and recommendations
#         recommendations = hits.assign(
#             video_link=hits.apply(
#                 lambda x: f"https://www.youtube.com/watch?v={self.corpus.loc[self.corpus[x['type']] == self.corpus[x['type']].unique()[x['corpus_id']]].index.get_level_values('videoId').to_list().pop()}",
#                 axis=1,
#             ),
#             likes=hits.apply(
#                 lambda x: self.corpus.loc[
#                     self.corpus[x["type"]]
#                     == self.corpus[x["type"]].unique()[x["corpus_id"]]
#                 ]
#                 .likeCount.to_list()
#                 .pop(),
#                 axis=1,
#             ),
#             comment_count=hits.apply(
#                 lambda x: self.corpus.loc[
#                     self.corpus[x["type"]]
#                     == self.corpus[x["type"]].unique()[x["corpus_id"]]
#                 ]
#                 .commentCount.to_list()
#                 .pop(),
#                 axis=1,
#             ),
#             views=hits.apply(
#                 lambda x: self.corpus.loc[
#                     self.corpus[x["type"]]
#                     == self.corpus[x["type"]].unique()[x["corpus_id"]]
#                 ]
#                 .viewCount.to_list()
#                 .pop(),
#                 axis=1,
#             ),
#             video_title=hits.apply(
#                 lambda x: self.corpus.loc[
#                     self.corpus[x["type"]]
#                     == self.corpus[x["type"]].unique()[x["corpus_id"]]
#                 ]
#                 .video_title.to_list()
#                 .pop(),
#                 axis=1,
#             ),
#             video_description=hits.apply(
#                 lambda x: self.corpus.loc[
#                     self.corpus[x["type"]]
#                     == self.corpus[x["type"]].unique()[x["corpus_id"]]
#                 ]
#                 .video_description.to_list()
#                 .pop(),
#                 axis=1,
#             ),
#         )
#         recommendations = recommendations.drop_duplicates(subset=["video_link"])
#         return (hits, recommendations)


# class PodcastRecommender(BaseRecommender):
#     def __init__(self):
#         super(PodcastRecommender, self).__init__()

#     def search(
#         self, question: str, corpus: str, top_k: int
#     ) -> Tuple[pd.DataFrame, pd.DataFrame]:
#         """
#         semantic search
#         """
#         assert (
#             corpus in self.corpus_embeddings_dict
#         ), f"Embeddings for [{corpus}] not found, please fit [{corpus}] first using the .fit() call"
#         question_embedding = self._encode(question, verbosity=False)
#         hits = self._semamtic_search(question_embedding, corpus, top_k)

#         # score all retrieved passages with the cross_encoder
#         cross_inp = [[question, self.corpus[corpus][hit["corpus_id"]]] for hit in hits]
#         cross_scores = self.cross_encoder.predict(cross_inp)

#         # sort results by the cross-encoder scores
#         for idx in range(len(cross_scores)):
#             hits[idx]["cross-score"] = cross_scores[idx]
#             hits[idx]["snippet"] = self.corpus[corpus][hits[idx]["corpus_id"]].replace(
#                 "\n", " "
#             )

#         # return hits and recommendations
#         hits = (
#             pd.DataFrame(hits)
#             .sort_values("cross-score", ascending=False)
#             .query("`cross-score` >= 0.0")
#         )
#         recommendations = hits.assign(
#             podcast_link=hits.corpus_id.apply(
#                 lambda x: self.corpus.loc[
#                     self.corpus.index.get_level_values(0)[x]
#                 ].audio_url.to_list()[0]
#             ),
#             snippet=hits.corpus_id.apply(lambda x: self.corpus.block.iloc[x]),
#             start=hits.corpus_id.apply(lambda x: self.corpus.start_time.iloc[x]),
#             end=hits.corpus_id.apply(lambda x: self.corpus.end_time.iloc[x]),
#         ).sort_values("start")
#         recommendations = (
#             recommendations.groupby("podcast_link", as_index=False)
#             .agg({"start": "min", "end": "max", "cross-score": "max"})
#             .sort_values("cross-score", ascending=False)
#         )
#         return (hits, recommendations)

#     def explore(
#         self, query: str, corpus: List[str], top_k: int
#     ) -> Tuple[pd.DataFrame, pd.DataFrame]:
#         assert all(corpus_str in self.corpus_embeddings_dict for corpus_str in corpus)
#         question_embedding = self._encode(query, verbosity=False)

#         # get hits
#         question_embedding = self._encode(query, verbosity=False)
#         hits = pd.concat(
#             [
#                 pd.DataFrame(
#                     self._semamtic_search(question_embedding, corpus_str, top_k=10)
#                 )
#                 for corpus_str in corpus
#             ],
#             axis=1,
#         )

#         # format hits
#         hits.columns = (" score ".join(corpus) + " score ").strip().split()
#         hits_corpus = pd.DataFrame(hits.loc[:, corpus].stack()).reset_index()
#         hits_score = pd.DataFrame(hits.loc[:, ["score"]].stack()).reset_index(drop=True)
#         hits = pd.concat([hits_corpus, hits_score], axis=1).drop(columns=["level_0"])
#         hits.columns = ["type", "corpus_id", "score"]
#         hits.sort_values("score", ascending=False, inplace=True)

#         # return hits and recommendations
#         recommendations = hits.assign(
#             podcast_link=hits.apply(
#                 lambda x: self.corpus.loc[
#                     self.corpus.loc[
#                         self.corpus[x["type"]]
#                         == self.corpus[x["type"]].unique()[x["corpus_id"]]
#                     ]
#                     .index.get_level_values(0)
#                     .to_list()
#                     .pop()
#                 ]
#                 .audio_url.to_list()
#                 .pop(),
#                 axis=1,
#             ),
#             share_link=hits.apply(
#                 lambda x: self.corpus.loc[
#                     self.corpus[x["type"]]
#                     == self.corpus[x["type"]].unique()[x["corpus_id"]]
#                 ]
#                 .share_url.to_list()
#                 .pop(),
#                 axis=1,
#             ),
#             video_title=hits.apply(
#                 lambda x: self.corpus.loc[
#                     self.corpus[x["type"]]
#                     == self.corpus[x["type"]].unique()[x["corpus_id"]]
#                 ]
#                 .title.to_list()
#                 .pop(),
#                 axis=1,
#             ),
#             video_description=hits.apply(
#                 lambda x: self.corpus.loc[
#                     self.corpus[x["type"]]
#                     == self.corpus[x["type"]].unique()[x["corpus_id"]]
#                 ]
#                 .excerpt.to_list()
#                 .pop(),
#                 axis=1,
#             ),
#         )
#         recommendations = recommendations.drop_duplicates(subset=["podcast_link"])
#         return (hits, recommendations)