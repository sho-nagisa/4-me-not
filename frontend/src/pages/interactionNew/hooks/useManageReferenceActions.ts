import { useCallback, useState, type Dispatch, type SetStateAction } from "react";

import {
  createCommunity,
  createPerson,
  createTopic,
  deleteCommunity,
  deletePerson,
  updateCommunityHidden,
  updatePersonHidden,
} from "../interactionsApi";
import type { Community, ManagePanelId, PageId, Person } from "../types";

type UseManageReferenceActionsParams = {
  refreshAll: () => Promise<void>;
  setPersonId: Dispatch<SetStateAction<string>>;
  setDetailPersonId: Dispatch<SetStateAction<string>>;
  setCurrentPage: Dispatch<SetStateAction<PageId>>;
  setManagePanel: Dispatch<SetStateAction<ManagePanelId>>;
  setCommunityId: Dispatch<SetStateAction<string>>;
  setTopicId: Dispatch<SetStateAction<string>>;
  onError: (message: string) => void;
  onSuccess: (message: string) => void;
};

export function useManageReferenceActions({
  refreshAll,
  setPersonId,
  setDetailPersonId,
  setCurrentPage,
  setManagePanel,
  setCommunityId,
  setTopicId,
  onError,
  onSuccess,
}: UseManageReferenceActionsParams) {
  const [newPersonName, setNewPersonName] = useState("");
  const [newPersonPrimaryCommunityId, setNewPersonPrimaryCommunityId] =
    useState("");
  const [newCommunityName, setNewCommunityName] = useState("");
  const [newCommunityParentId, setNewCommunityParentId] = useState("");
  const [newTopicName, setNewTopicName] = useState("");
  const [newTopicParentId, setNewTopicParentId] = useState("");
  const [isCreatingPerson, setIsCreatingPerson] = useState(false);
  const [isCreatingCommunity, setIsCreatingCommunity] = useState(false);
  const [isCreatingTopic, setIsCreatingTopic] = useState(false);
  const [personActionId, setPersonActionId] = useState<string | null>(null);
  const [communityActionId, setCommunityActionId] = useState<string | null>(null);

  const handleCreatePerson = useCallback(async () => {
    if (!newPersonName.trim()) {
      onError("追加する人の名前を入力してください。");
      return;
    }

    setIsCreatingPerson(true);
    try {
      const person = await createPerson({
        name: newPersonName.trim(),
        primary_community_id: newPersonPrimaryCommunityId || null,
      });
      setNewPersonName("");
      setNewPersonPrimaryCommunityId("");
      await refreshAll();
      setPersonId(person.id);
      setDetailPersonId(person.id);
      setCurrentPage("manage");
      setManagePanel("people");
      onSuccess("人を追加しました。");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "人の追加に失敗しました。";
      onError(message);
    } finally {
      setIsCreatingPerson(false);
    }
  }, [
    newPersonName,
    newPersonPrimaryCommunityId,
    onError,
    onSuccess,
    refreshAll,
    setCurrentPage,
    setDetailPersonId,
    setManagePanel,
    setPersonId,
  ]);

  const handleCreateCommunity = useCallback(async () => {
    if (!newCommunityName.trim()) {
      onError("追加するコミュニティ名を入力してください。");
      return;
    }

    setIsCreatingCommunity(true);
    try {
      const community = await createCommunity({
        name: newCommunityName.trim(),
        parent_id: newCommunityParentId || null,
      });
      setNewCommunityName("");
      setNewCommunityParentId("");
      await refreshAll();
      setCommunityId(community.id);
      onSuccess("コミュニティを追加しました。");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "コミュニティの追加に失敗しました。";
      onError(message);
    } finally {
      setIsCreatingCommunity(false);
    }
  }, [
    newCommunityName,
    newCommunityParentId,
    onError,
    onSuccess,
    refreshAll,
    setCommunityId,
  ]);

  const handleCreateTopic = useCallback(async () => {
    if (!newTopicName.trim()) {
      onError("追加する話題名を入力してください。");
      return;
    }

    setIsCreatingTopic(true);
    try {
      const topic = await createTopic({
        name: newTopicName.trim(),
        parent_id: newTopicParentId || null,
      });
      setNewTopicName("");
      setNewTopicParentId("");
      await refreshAll();
      setTopicId(topic.id);
      onSuccess("話題を追加しました。");
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "話題の追加に失敗しました。";
      onError(message);
    } finally {
      setIsCreatingTopic(false);
    }
  }, [
    newTopicName,
    newTopicParentId,
    onError,
    onSuccess,
    refreshAll,
    setTopicId,
  ]);

  const handleTogglePersonHidden = useCallback(
    async (person: Person) => {
      setPersonActionId(person.id);
      try {
        await updatePersonHidden(person.id, !person.is_hidden);

        await refreshAll();
        onSuccess(
          person.is_hidden ? "人物を再表示しました。" : "人物を非表示にしました。"
        );
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "人物状態の更新に失敗しました。";
        onError(message);
      } finally {
        setPersonActionId(null);
      }
    },
    [onError, onSuccess, refreshAll]
  );

  const handleDeletePerson = useCallback(
    async (person: Person) => {
      if (
        !window.confirm(
          `${person.name} を削除しますか？ この人の関連記録も削除されます。`
        )
      ) {
        return;
      }

      setPersonActionId(person.id);
      try {
        await deletePerson(person.id);

        await refreshAll();
        onSuccess("人物を削除しました。");
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "人物削除に失敗しました。";
        onError(message);
      } finally {
        setPersonActionId(null);
      }
    },
    [onError, onSuccess, refreshAll]
  );

  const handleToggleCommunityHidden = useCallback(
    async (community: Community) => {
      setCommunityActionId(community.id);
      try {
        await updateCommunityHidden(community.id, !community.is_hidden);

        await refreshAll();
        onSuccess(
          community.is_hidden
            ? "コミュニティを再表示しました。"
            : "コミュニティを非表示にしました。"
        );
      } catch (error) {
        const message =
          error instanceof Error
            ? error.message
            : "コミュニティ状態の更新に失敗しました。";
        onError(message);
      } finally {
        setCommunityActionId(null);
      }
    },
    [onError, onSuccess, refreshAll]
  );

  const handleDeleteCommunity = useCallback(
    async (community: Community) => {
      if (
        !window.confirm(
          `${community.name} を削除しますか？ 関連する所属やコミュニティ参照が外れる場合があります。`
        )
      ) {
        return;
      }

      setCommunityActionId(community.id);
      try {
        await deleteCommunity(community.id);

        await refreshAll();
        onSuccess("コミュニティを削除しました。");
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "コミュニティ削除に失敗しました。";
        onError(message);
      } finally {
        setCommunityActionId(null);
      }
    },
    [onError, onSuccess, refreshAll]
  );

  return {
    newPersonName,
    setNewPersonName,
    newPersonPrimaryCommunityId,
    setNewPersonPrimaryCommunityId,
    newCommunityName,
    setNewCommunityName,
    newCommunityParentId,
    setNewCommunityParentId,
    newTopicName,
    setNewTopicName,
    newTopicParentId,
    setNewTopicParentId,
    isCreatingPerson,
    isCreatingCommunity,
    isCreatingTopic,
    personActionId,
    communityActionId,
    handleCreatePerson,
    handleCreateCommunity,
    handleCreateTopic,
    handleTogglePersonHidden,
    handleDeletePerson,
    handleToggleCommunityHidden,
    handleDeleteCommunity,
  };
}
