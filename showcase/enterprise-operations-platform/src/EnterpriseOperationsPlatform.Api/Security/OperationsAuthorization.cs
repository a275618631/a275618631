namespace EnterpriseOperationsPlatform.Api.Security;

public static class OperationsAuthorization
{
    public const string ReadPolicy = "Operations.Read";
    public const string WritePolicy = "Operations.Write";
    public const string CompletePolicy = "Operations.Complete";

    public const string Viewer = "OperationsViewer";
    public const string Operator = "OperationsOperator";
    public const string Supervisor = "OperationsSupervisor";
    public const string Administrator = "OperationsAdmin";
}
